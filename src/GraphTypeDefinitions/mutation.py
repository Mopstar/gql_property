import dataclasses
import typing

import strawberry

from .EventGQLModel import EventMutation
from .EventInvitationGQLModel import EventInvitationMutation
from .PurchaseGQLModel import PurchaseGQLModel, PurchaseInsertGQLModel
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getLoadersFromInfo, getUserFromInfo

from src.DBDefinitions.purchasemodel import PurchaseModel, PurchaseItem


@strawberry.type(description="""Type for mutation root""")
class Mutation(EventMutation, EventInvitationMutation):
    @strawberry.mutation(
        description="Insert a Purchase",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_insert(self, info: strawberry.Info, purchase: PurchaseInsertGQLModel) -> PurchaseGQLModel:
        loaders = getLoadersFromInfo(info)
        acting_user = None
        try:
            acting_user = getUserFromInfo(info)
        except AssertionError:
            acting_user = None

        payload = dataclasses.asdict(purchase)
        items = payload.pop("subinfo", []) or []

        if acting_user and not payload.get("requester_id"):
            payload["requester_id"] = acting_user.get("id")

        purchase_data = {key: value for key, value in payload.items() if value is not None}
        purchase_model = PurchaseModel(**purchase_data)
        new_purchase = await loaders.PurchaseModel.insert(purchase_model)

        for item in items:
            item_data = {key: value for key, value in item.items() if value is not None}
            item_data["purchase_id"] = new_purchase.id
            purchase_item = PurchaseItem(**item_data)
            await loaders.PurchaseItem.insert(purchase_item)

        return PurchaseGQLModel.from_dataclass(new_purchase)

