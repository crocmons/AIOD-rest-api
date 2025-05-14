"""synchronize identifiers

Revision ID: 8b054cdc9261
Revises: 1662d64ebe23
Create Date: 2025-05-14 09:07:47.064937

"""

from typing import Sequence, Union, NamedTuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, text
from sqlmodel import Session

from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses

# revision identifiers, used by Alembic.
revision: str = "8b054cdc9261"
down_revision: Union[str, None] = "1662d64ebe23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class ParentTable(NamedTuple):
    name: str
    fk_identifier: str
    children: list[str]


def upgrade() -> None:
    # For more information, see docs/developer/schema/index.md#a-note-on-identifiers
    # We store a map for the old->new identifiers so we can support backwards compatibility (maybe)
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
    for parent in [aiod_concept, ai_resource, ai_asset, agent]:
        for table in parent.children:
            identifier_map_table_name = f"_{table}_{parent.name}_identifier_map"
            op.create_table(
                identifier_map_table_name,
                Column("old_identifier", Integer, index=True),
                Column("new_identifier", Integer, index=True),
            )
            op.execute(
                text(
                    f"INSERT INTO {identifier_map_table_name} "  # noqa: S608  # no user input
                    f"SELECT {parent.fk_identifier} as old_identifier, aiod_entry_identifier as new_identifier "
                    f"FROM {table};"
                ),
            )

    # Update Foreign Key Constraint to ON UPDATE CASCADE
    with Session(op.get_bind()) as session:
        for table in [agent, ai_resource, ai_asset]:
            rows = session.scalars(
                text(
                    "SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME "
                    "FROM information_schema.KEY_COLUMN_USAGE "
                    "WHERE REFERENCED_TABLE_NAME='{table.name}' "
                    "AND REFERENCED_COLUMN_NAME='identifier';"
                )
            )
            for constraint, from_table, from_column in rows:
                op.execute(f"ALTER TABLE {from_table} DROP FOREIGN KEY {constraint};")
                op.execute(
                    f"ALTER TABLE {from_table} "
                    f"ADD CONSTRAINT {constraint} "
                    f"FOREIGN KEY {from_column} REFERENCES {table}(identifier) "
                    f"ON DELETE CASCADE "
                    f"ON UPDATE CASCADE;"
                )

    # Actually set the new keys
    ...  # base tables. agent, resource, asset
    pass


def downgrade() -> None:
    pass
