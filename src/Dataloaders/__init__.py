# from uoishelpers.dataloaders import createIdLoader, createFkeyLoader
# from functools import cache

from src.DBDefinitions import BaseModel
from src.DBDefinitions import (
    EventModel,
    EventInvitationModel,

)
from src.DBDefinitions import purchasemodel
from src.DBDefinitions.purchasemodel import PurchaseModel, PurchaseItem

from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader
from uoishelpers.schema.ProfilingExtension import Counter
import src.DBDefinitions


class LoaderMap(LoaderMapBase[BaseModel]):
    """LoaderMap is a map of IDLoaders for all models in the BaseModel registry.
    It is used to create loaders for all models in the BaseModel registry.
    """
    BaseModel = BaseModel

    EventModel: IDLoader[src.DBDefinitions.EventModel] = None
    EventInvitationModel: IDLoader[src.DBDefinitions.EventInvitationModel] = None
    PurchaseModel: IDLoader[src.DBDefinitions.purchasemodel.PurchaseModel] = None
    PurchaseItem: IDLoader[src.DBDefinitions.purchasemodel.PurchaseItem] = None
    PurchaseItemModel: IDLoader[src.DBDefinitions.purchasemodel.PurchaseItem] = None  # Alias for PurchaseItem

    def __init__(self, session):
        super().__init__(session)

        self.EventModel = self.get(EventModel)
        self.EventInvitationModel = self.get(EventInvitationModel)
        self.PurchaseModel = self.get(PurchaseModel)
        self.PurchaseItem = self.get(PurchaseItem)
        self.PurchaseItemModel = self.PurchaseItem  # Alias for compatibility

        # print(f"LoaderMap created with session: {session}")


def createLoadersContext(session_like):
    session = session_like
    created_session = False
    if not hasattr(session, "identity_map") and callable(session_like):
        session = session_like()
        created_session = True
    context = {
        "loaders": LoaderMap(session),
        "ProfilingExtension.counter": Counter(),
    }
    if created_session:
        context.setdefault("session", session)
    return context
