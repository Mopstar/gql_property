import strawberry


from .EventGQLModel import EventMutation
from .EventInvitationGQLModel import EventInvitationMutation
from .PurchaseGQLModel import PurchaseMutation



@strawberry.type(description="""Type for mutation root""")
class Mutation(EventMutation, EventInvitationMutation, PurchaseMutation):
    pass