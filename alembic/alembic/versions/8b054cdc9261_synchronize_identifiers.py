"""synchronize identifiers

Revision ID: 8b054cdc9261
Revises: 1662d64ebe23
Create Date: 2025-05-14 09:07:47.064937

"""
import logging
# no user input
# ruff: noqa: S608
from typing import Sequence, Union, NamedTuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, text
from sqlmodel import Session

from database.session import DbSession
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses

# revision identifiers, used by Alembic.
revision: str = "8b054cdc9261"
down_revision: Union[str, None] = "1662d64ebe23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic")


class ParentTable(NamedTuple):
    name: str
    fk_identifier: str
    children: list[str]


def upgrade() -> None:
    # For more information, see docs/developer/schema/index.md#a-note-on-identifiers
    aiod_concept = ParentTable(
        name="aiod_concept",
        fk_identifier="identifier",
        children=[
            "contact",
            "organisation",
            "person",
            "dataset",
            "publication",
            "case_study",
            "computational_asset",
            "experiment",
            "ml_model",
            "educational_resource",
            "event",
            "news",
            "project",
            "service",
            "team",
            "resource_bundle",
        ],
    )
    ai_resource = ParentTable(
        name="ai_resource",
        fk_identifier="ai_resource_id",
        children=[
            "organisation",
            "person",
            "dataset",
            "publication",
            "case_study",
            "computational_asset",
            "experiment",
            "ml_model",
            "educational_resource",
            "event",
            "news",
            "project",
            "service",
            "team",
            "resource_bundle",
        ],
    )
    ai_asset = ParentTable(
        name="ai_asset",
        fk_identifier="ai_asset_id",
        children=[
            "dataset",
            "publication",
            "case_study",
            "computational_asset",
            "experiment",
            "ml_model",
        ],
    )
    agent = ParentTable(
        name="agent",
        fk_identifier="agent_id",
        children=["organisation", "person"],
    )
    abbreviations = {
        "contact": "con",
        "organisation": "org",
        "person": "prsn",
        "dataset": "data",
        "publication": "pub",
        "case_study": "case",
        "computational_asset": "comp",
        "experiment": "exp",
        "ml_model": "mdl",
        "educational_resource": "edu",
        "event": "evnt",
        "news": "news",
        "project": "proj",
        "service": "srvc",
        "team": "team",
        "resource_bundle": "res",
    }
    # We store a map for the old->new identifiers so we can support backwards compatibility (maybe)
    # For regular identifiers, we store this per concept, as this is how they are likely accessed
    # (e.g., /dataset/1). For parent identifiers we store it all together for parent routers.
    # TODO: Actually generate new identifiers
    for child in aiod_concept.children:
        logger.info(f"Creating conversion table for {child}")
        map_table = f"_{child}_identifier_map"
        op.create_table(
            map_table,
            Column("old", Integer, index=True),
            Column("new", Integer, index=True),
        )
        op.execute(
            f"INSERT INTO {map_table} SELECT identifier, aiod_entry_identifier FROM {child} "
        )

    for parent in [ai_resource, ai_asset, agent]:
        logger.info(f"Creating conversion table for {parent.name}")
        map_table = f"_{parent.name}_identifier_map"
        op.create_table(
            map_table,
            Column("old", Integer, index=True),
            Column("new", Integer, index=True),
        )
        child_data = "UNION ".join(
            f"SELECT {parent.fk_identifier}, aiod_entry_identifier FROM {child_table} "
            for child_table in parent.children
        )
        op.execute(f"INSERT INTO {map_table} SELECT * FROM ({child_data}) as child")

    # Now we can continue with data migration
    # First we delete a conflicting CHECK constraint: https://github.com/aiondemand/AIOD-rest-api/issues/518
    logger.info("Dropping contact CHECK constraint.")
    op.execute(
        "ALTER TABLE contact DROP CONSTRAINT contact_person_and_organisation_not_both_filled"
    )

    # Then we update foreign key constraints to ON UPDATE CASCADE to make data migration easier
    with DbSession() as session:
        tables_with_referenced_key = [
            agent.name,
            ai_asset.name,
            ai_resource.name,
            *aiod_concept.children,
        ]
        logger.info("Fetching existing foreign key constraints.")
        constraints = session.execute(
            text(
                "SELECT refs.CONSTRAINT_NAME, refs.DELETE_RULE, kcu.TABLE_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME, kcu.REFERENCED_COLUMN_NAME "
                "FROM information_schema.REFERENTIAL_CONSTRAINTS as refs "
                "JOIN information_schema.KEY_COLUMN_USAGE as kcu "
                "ON refs.CONSTRAINT_NAME=kcu.CONSTRAINT_NAME "
                f"WHERE refs.REFERENCED_TABLE_NAME IN ({', '.join(map(repr, tables_with_referenced_key))});"
            )
        )
    constraints = list(constraints)
    logger.info(f"Dropping {len(constraints)} foreign key constraints.")
    for constraint, delete_rule, from_table, from_column, to_table, to_column in constraints:
        op.execute(f"ALTER TABLE {from_table} DROP FOREIGN KEY {constraint}")

    updated_columns = set()
    for constraint, delete_rule, from_table, from_column, to_table, to_column in constraints:
        for table, column in [(to_table, to_column), (from_table, from_column)]:
            if (table, column) not in updated_columns:
                logger.info(f"Altering {table}.{column} to VARCHAR(40).")
                op.execute(f"ALTER TABLE {table} CHANGE COLUMN {column} {column} VARCHAR(40);")
                updated_columns.add((table, column))

    for constraint, delete_rule, from_table, from_column, to_table, to_column in constraints:
        logger.info(f"Adding back constraint {constraint}.")
        op.execute(
            f"ALTER TABLE {from_table} "
            f"ADD CONSTRAINT {constraint} "
            f"FOREIGN KEY ({from_column}) REFERENCES {to_table}({to_column}) "
            f"ON DELETE {delete_rule} "
            f"ON UPDATE CASCADE;"
        )

    # And finally we can do data migration: we update the primary keys in the main tables,
    # the remainder of the references should now be taken care of with ON UPDATE CASCADE.
    # We cannot directly set identifiers to be aiod_entry_identifiers: those ranges overlap,
    # which leads to (temporary) duplicate keys. To avoid that, we add a temporary offset during
    # the update, and recover the original identifier afterwards.
    for table in aiod_concept.children:
        logger.info(f"Assigning new identifiers to {table}.")
        op.execute(
            f"UPDATE {table} SET identifier=CONCAT('{abbreviations[table]}', '_', aiod_entry_identifier)"
        )

    for table in [agent, ai_asset, ai_resource]:
        child_data = "UNION ".join(
            f"SELECT {table.fk_identifier}, identifier FROM {child_table} "
            for child_table in table.children
        )
        logger.info(f"Assigning new identifiers to {table.name}.")
        op.execute(
            f"UPDATE {table.name} "
            f"JOIN ({child_data}) as child "
            f"ON {table.name}.identifier=child.{table.fk_identifier} "
            f"SET {table.name}.identifier=child.identifier;"
        )


def downgrade() -> None:
    pass
