import typing
import datetime
import dataclasses
import sqlalchemy
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, synonym

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, column_property

from .BaseModel import BaseModel, UUIDColumn, UUIDFKey, IDType

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#
###########################################################################################################################
class PurchaseModel(BaseModel):
    __tablename__ = "purchases"
    path_attribute_name = "path"
    parent_attribute_name = "maininfo"
    parent_id_attribute_name = "maininfo_id"
    children_attribute_name = "subinfo"


    reason: Mapped[str] = mapped_column(default=None, nullable=True)
    description: Mapped[str] = mapped_column(default=None, nullable=True)
    correct_examples: Mapped[str] = mapped_column(default=None, nullable=True)
    other_info_website: Mapped[str] = mapped_column(default=None, nullable=True)
    handover_request: Mapped[datetime.datetime] = mapped_column(default=None, nullable=True)
    reasoning: Mapped[str] = mapped_column(default=None, nullable=True)

    masterevent_id: Mapped[IDType] = mapped_column(
        ForeignKey("purchases.id"),
        nullable=True,
        default=None,
        index=True,
    )


    masterevent = relationship(
        "PurchaseModel",
        viewonly=True, 
        remote_side="PurchaseModel.id",
        uselist=False,
        back_populates="subinfo",
    )
    