from database.model.concept.concept import AIoDConcept
from database.model.named_relation import NamedRelation

class CompanyRevenue(AIoDConcept, NamedRelation, table=True):
    __tablename__ = "company_revenue"
