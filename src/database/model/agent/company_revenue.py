# from database.model.concept.concept import AIoDConcept, AIoDConceptBase

# class CompanyRevenueBase(AIoDConceptBase):
#     """
#     """

# class CompanyRevenue(CompanyRevenueBase, AIoDConcept, table=True): # type: ignore [call-arg]
#     __tablename__ = "company_revenue"


from database.model.named_relation import NamedRelation


class CompanyRevenue(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "company_revenue"
