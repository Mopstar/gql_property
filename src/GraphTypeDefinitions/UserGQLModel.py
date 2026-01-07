import typing
import strawberry
from .BaseGQLModel import IDType


from uoishelpers.gqlpermissions import (
    OnlyForAuthentized
)
from uoishelpers.resolvers import (
    VectorResolver,
    getLoadersFromInfo,
)
from .EventInvitationGQLModel import EventInvitationGQLModel, EventInvitationInputFilter

EventGQLModel = typing.Annotated["EventGQLModel", strawberry.lazy(".EventGQLModel")]

@strawberry.federation.type(extend=True, keys=["id"])
class UserGQLModel:
    id: IDType = strawberry.federation.field(external=True)

    from .BaseGQLModel import resolve_reference

    event_invitations: typing.List[EventInvitationGQLModel] = strawberry.field(
        description="Links to events where the user has been invited",
        permission_classes=[
            OnlyForAuthentized
        ],
        resolver=VectorResolver[EventInvitationGQLModel](fkey_field_name="user_id", whereType=EventInvitationInputFilter)
    )

    # async def event_invitations(self, info:strawberry.types.Info)
    @strawberry.field(
        description="Events associated with the user via invitations",
        permission_classes=[OnlyForAuthentized]
    )
    async def events(self, info: strawberry.types.Info) -> typing.List[EventGQLModel]:
        loaders = getLoadersFromInfo(info)
        invitation_loader = loaders.EventInvitationModel
        invitations_iter = await invitation_loader.filter_by(user_id=self.id)
        invitations = list(invitations_iter)
        event_ids = []
        for invitation in invitations:
            event_id = getattr(invitation, "event_id", None)
            if event_id is None:
                continue
            event_ids.append(event_id)
        seen = set()
        unique_event_ids = []
        for value in event_ids:
            if value in seen:
                continue
            seen.add(value)
            unique_event_ids.append(value)
        event_loader = loaders.EventModel
        results: typing.List[EventGQLModel] = []
        from .EventGQLModel import EventGQLModel as _EventGQLModel
        for event_id in unique_event_ids:
            db_row = await event_loader.load(event_id)
            if db_row is None:
                continue
            results.append(_EventGQLModel.from_dataclass(db_row))
        return results
