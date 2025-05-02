from database.model.named_relation import NamedRelation

class CompanyRevenue(NamedRelation, table=True):
    __tablename__ = "company_revenue"
