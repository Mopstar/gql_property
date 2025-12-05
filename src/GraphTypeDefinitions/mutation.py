import dataclasses
import typing
import uuid

import strawberry

from .EventGQLModel import EventMutation
from .EventInvitationGQLModel import EventInvitationMutation
from .PurchaseGQLModel import (
    PurchaseGQLModel,
    PurchaseInsertGQLModel,
    PurchaseUpdateGQLModel,
    PurchaseDeleteGQLModel,
)
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import (
    DeleteError,
    UpdateError,
    getLoadersFromInfo,
    getUserFromInfo,
)

from src.DBDefinitions.purchasemodel import PurchaseModel, PurchaseItem
from src.Dataloaders import LoaderMap



def _coerce_uuid(value: typing.Optional[typing.Union[str, uuid.UUID]]) -> typing.Optional[uuid.UUID]:
    if value is None or isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


async def _sync_purchase_items(
    loaders,
    purchase_id: uuid.UUID,
    items_payload: typing.List[typing.Dict[str, typing.Any]],
    acting_user_id: typing.Optional[uuid.UUID],
):
    """Replace purchase items with provided collection."""
    existing_items = list(await loaders.PurchaseItem.filter_by(purchase_id=purchase_id))
    existing_map = {item.id: item for item in existing_items}
    preserved_ids: set[uuid.UUID] = set()

    for item in items_payload:
        item_data = {key: value for key, value in item.items() if value is not None}
        raw_id = item_data.get("id")
        if isinstance(raw_id, str):
            raw_id = uuid.UUID(raw_id)
            item_data["id"] = raw_id

        if raw_id:
            db_row = existing_map.get(raw_id)
            if db_row is None:
                raise ValueError(f"Purchase item with id {raw_id} does not exist")
            if not item_data.get("lastchange"):
                raise ValueError("Missing lastchange value for purchase item update")
            if acting_user_id:
                item_data["changedby_id"] = acting_user_id
            item_data["purchase_id"] = purchase_id

            purchase_item = PurchaseItem(**item_data)
            result = await loaders.PurchaseItem.update(purchase_item)
            if result is None:
                raise ValueError("Purchase item update failed due to concurrent modification")
            preserved_ids.add(raw_id)
        else:
            item_data["purchase_id"] = purchase_id
            if acting_user_id:
                item_data["createdby_id"] = acting_user_id
            purchase_item = PurchaseItem(**item_data)
            await loaders.PurchaseItem.insert(purchase_item)

    for row in existing_items:
        if row.id not in preserved_ids:
            await loaders.PurchaseItem.delete(row.id)

    fkey_loader = loaders.PurchaseItem.createFkeySpecificLoader(
        fkey="purchase_id",
        session=loaders.PurchaseItem.session,
    )
    fkey_loader.clear(purchase_id)
    await fkey_loader.load(purchase_id)


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

        acting_user_id = _coerce_uuid(acting_user.get("id")) if acting_user else None
        if acting_user_id and not payload.get("requester_id"):
            payload["requester_id"] = acting_user_id

        for key in ("id", "requester_id", "approver_id", "maininfo_id"):
            if payload.get(key):
                payload[key] = _coerce_uuid(payload[key])

        purchase_data = {key: value for key, value in payload.items() if value is not None}
        purchase_model = PurchaseModel(**purchase_data)
        new_purchase = await loaders.PurchaseModel.insert(purchase_model)

        for item in items:
            item_data = {key: value for key, value in item.items() if value is not None}
            item_data["purchase_id"] = new_purchase.id
            purchase_item = PurchaseItem(**item_data)
            await loaders.PurchaseItem.insert(purchase_item)

        return PurchaseGQLModel.from_dataclass(new_purchase)

    @strawberry.mutation(
        description="Update an existing purchase",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_update(
        self,
        info: strawberry.Info,
        purchase: PurchaseUpdateGQLModel,
    ) -> typing.Union[PurchaseGQLModel, UpdateError[PurchaseGQLModel]]:
        loaders = getLoadersFromInfo(info)
        try:
            acting_user = getUserFromInfo(info)
        except AssertionError:
            acting_user = None

        payload = dataclasses.asdict(purchase)
        items_payload = payload.pop("subinfo", None)

        purchase_id = _coerce_uuid(payload.get("id"))
        payload["id"] = purchase_id
        acting_user_id = _coerce_uuid(acting_user.get("id")) if acting_user else None

        if acting_user_id:
            payload["changedby_id"] = acting_user_id

        for key in ("requester_id", "approver_id", "maininfo_id"):
            if payload.get(key):
                payload[key] = _coerce_uuid(payload[key])

        purchase_data = {key: value for key, value in payload.items() if value is not None}
        purchase_model = PurchaseModel(**purchase_data)
        updated_purchase = await loaders.PurchaseModel.update(purchase_model)

        if updated_purchase is None:
            entity = await PurchaseGQLModel.resolve_reference(info=info, id=purchase_data["id"])
            return UpdateError[PurchaseGQLModel](_entity=entity, msg="Purchase update failed", _input=purchase)

        if items_payload is not None:
            try:
                await _sync_purchase_items(
                    loaders=loaders,
                    purchase_id=purchase_data["id"],
                    items_payload=items_payload,
                    acting_user_id=acting_user_id,
                )
            except ValueError as exc:
                entity = PurchaseGQLModel.from_dataclass(updated_purchase)
                return UpdateError[PurchaseGQLModel](_entity=entity, msg=str(exc), _input=purchase)

        return PurchaseGQLModel.from_dataclass(updated_purchase)

    @strawberry.mutation(
        description="Delete a purchase",
        permission_classes=[OnlyForAuthentized]
    )
    async def purchase_delete(
        self,
        info: strawberry.Info,
        purchase: PurchaseDeleteGQLModel
    ) -> typing.Optional[DeleteError[PurchaseGQLModel]]:
        loaders = getLoadersFromInfo(info)
        purchase_id = _coerce_uuid(purchase.id)

        db_row = await loaders.PurchaseModel.load(purchase_id)
        if db_row is None:
            return DeleteError[PurchaseGQLModel](_entity=None, msg="Purchase not found", _input=purchase)

        timestamp = getattr(db_row, "lastchange", None)
        if timestamp and timestamp != purchase.lastchange:
            gql_entity = PurchaseGQLModel.from_dataclass(db_row)
            return DeleteError[PurchaseGQLModel](
                _entity=gql_entity,
                msg="Purchase was modified by someone else",
                _input=purchase,
            )

        await loaders.PurchaseModel.delete(purchase_id)
        session = loaders.PurchaseModel.session
        if session:
            await session.flush()
            await session.commit()

            def _expunge_purchase(sync_session, pk):
                identity_key = sync_session.identity_key(PurchaseModel, (pk,))
                instance = sync_session.identity_map.get(identity_key)
                if instance is not None:
                    sync_session.expunge(instance)

            await session.run_sync(_expunge_purchase, purchase_id)
        deleted_ids = info.context.setdefault("deleted_purchases", set())
        deleted_ids.add(purchase_id)
        return None
