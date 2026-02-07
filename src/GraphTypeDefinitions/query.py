import strawberry


from .EventGQLModel import EventQuery
from .EventInvitationGQLModel import EventInvitationQuery
from .PurchaseGQLModel import PurchaseQuery
from .PurchaseTypeGQLModel import PurchaseTypeQuery
from .EventTypeGQLModel import EventTypeQuery


@strawberry.type(description="""Type for query root (admissions only)""")
class Query(EventQuery, EventInvitationQuery, PurchaseQuery, PurchaseTypeQuery, EventTypeQuery):
    pass