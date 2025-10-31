import datetime
import strawberry

from .query import Query
from .mutation import Mutation

timedelta = strawberry.scalar(
    # NewType("TimeDelta", float),
    datetime.timedelta,
    name="timedelta",
    serialize=lambda v: v.total_seconds() / 60,
    parse_value=lambda v: datetime.timedelta(minutes=v),
)


from .BaseGQLModel import Relation
from .BaseGQLModel import BaseGQLModel
from .UserGQLModel import UserGQLModel
from .PurchaseGQLModel import PurchaseGQLModel
from .PurchaseItemGQLModel import PurchaseItemGQLModel

schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    types=(UserGQLModel, BaseGQLModel, PurchaseGQLModel, PurchaseItemGQLModel), 
    scalar_overrides={datetime.timedelta: timedelta._scalar_definition},

    extensions=[],
    schema_directives=[Relation]
    
)

from uoishelpers.schema import WhoAmIExtension, ProfilingExtension, PrometheusExtension


class ResilientWhoAmIExtension(WhoAmIExtension):
    async def on_execute(self):
        query = self.execution_context.query
        print(f"Executing {query}")
        existing_user = self.execution_context.context.get("user", None)
        should_query_remote = (
            existing_user is None
            and query not in [self.apolloQuery, self.graphiQLQuery, self.sdlQuery]
        )

        resolved_user = existing_user
        if should_query_remote:
            try:
                whoami_response = await self.ug_query(query=self.mequery)
                resolved_user = whoami_response["data"]["me"]
            except Exception:
                print("error with ug endpoint")
                resolved_user = existing_user

        if not resolved_user:
            resolved_user = existing_user or {}

        self.execution_context.context["user"] = resolved_user
        self.execution_context.context.setdefault("ug_client", self.ug_query)
        yield


schema.extensions.append(ResilientWhoAmIExtension)
schema.extensions.append(ProfilingExtension)
schema.extensions.append(PrometheusExtension(prefix="GQL_Evolution"))

from uoishelpers.gqlpermissions.RolePermissionSchemaExtension import RolePermissionSchemaExtension
schema.extensions.append(RolePermissionSchemaExtension)

