from datetime import date
from typing import Optional, Literal

from sqlmodel import Field, Relationship

from database.model.named_relation import Taxonomy, create_taxonomy
from database.model.agent.agent import AgentBase, Agent
from database.model.agent.agent_table import AgentTable
from database.model.agent.contact import Contact
from database.model.agent.organisation_type import OrganisationType
from database.model.field_length import NORMAL, LONG
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToOne, ManyToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
    FindByIdentifierDeserializerList,
)


OrganisationTurnover: type[Taxonomy] = create_taxonomy(
    class_name="OrganisationTurnover", table_name="organisation_turnover"
)

EmployeeCount: type[Taxonomy] = create_taxonomy(
    class_name="EmployeeCount", table_name="employee_count"
)


class OrganisationBase(AgentBase):
    date_founded: date | None = Field(
        description="The date on which the organisation was founded.",
        schema_extra={"example": "2022-01-01"},
    )
    legal_name: str | None = Field(
        description="The official legal name of the organisation.",
        schema_extra={"example": "The Organisation Name"},
        max_length=NORMAL,
    )
    ai_relevance: str | None = Field(
        description="A description of positioning of the organisation within "
        "the broader European AI ecosystem.",
        schema_extra={"example": "Part of CLAIRE, focussing on explainable AI."},
        max_length=LONG,
    )


class Organisation(OrganisationBase, Agent, table=True):  # type: ignore [call-arg]
    __tablename__ = "organisation"
    __abbreviation__ = "org"

    contact_details: Optional[Contact] = Relationship(sa_relationship_kwargs={"uselist": False})

    type_identifier: int | None = Field(foreign_key=OrganisationType.__tablename__ + ".identifier")
    type: Optional[OrganisationType] = Relationship()

    member: list[AgentTable] = Relationship(
        link_model=many_to_many_link_factory(
            "organisation",
            AgentTable.__tablename__,
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )

    turnover_identifier: int | None = Field(
        default=None,
        foreign_key="organisation_turnover.identifier",
        description="The revenue bracket of the organisation.",
    )
    turnover: Optional[OrganisationTurnover] = Relationship()  # type: ignore[valid-type]

    number_of_employees_identifier: int | None = Field(
        default=None,
        foreign_key="employee_count.identifier",
        description="The employee size bracket of the organisation.",
    )
    number_of_employees: Optional[EmployeeCount] = Relationship()  # type: ignore[valid-type]

    class RelationshipConfig(Agent.RelationshipConfig):
        contact_details: str | None = OneToOne(
            description="The identifier of the contact details by which this organisation "
            "can be reached.",
            deserializer=FindByIdentifierDeserializer(Contact),
            _serializer=AttributeSerializer("identifier"),
        )
        type: Optional[str] = ManyToOne(
            description="The type of organisation.",
            identifier_name="type_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(OrganisationType),
            example="Research Institution",
        )
        member: list[str] = ManyToMany(
            description="The identifier of an agent (e.g. organisation or person) that is a "
            "member of this organisation.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AgentTable),
            default_factory_pydantic=list,
        )

        turnover: Optional[Literal["<1m €", ">1m €", ">3m €", ">5m €", ">50m €", ">1.5b €"]] = (
            ManyToOne(
                description="The approximate revenue bracket of the organisation in euros (e.g., '<1m €', '>1.5b €').",
                identifier_name="turnover_identifier",
                _serializer=AttributeSerializer("name"),
                deserializer=FindByNameDeserializer(OrganisationTurnover),
                example=">5m €",
            )
        )

        number_of_employees: Optional[Literal["<10", "<50", "<250", ">=250"]] = ManyToOne(
            description=(
                "The number of employees of the organisation. "
                "Allowed values: [<10, <50, <250, >=250]"
            ),
            identifier_name="number_of_employees_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(EmployeeCount),
            example="<10",
        )


deserializer = FindByIdentifierDeserializer(Organisation)
Contact.RelationshipConfig.organisation.deserializer = deserializer  # type: ignore
