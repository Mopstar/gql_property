import strawberry


from .EventGQLModel import EventQuery
from .EventInvitationGQLModel import EventInvitationQuery
from .PurchaseGQLModel import PurchaseQuery


@strawberry.type(description="""Type for query root (admissions only)""")
class Query(EventQuery, EventInvitationQuery, PurchaseQuery  ):
    pass