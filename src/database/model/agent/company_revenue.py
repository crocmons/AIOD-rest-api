from database.model.named_relation import NamedRelation


class CompanyRevenue(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "company_revenue"
