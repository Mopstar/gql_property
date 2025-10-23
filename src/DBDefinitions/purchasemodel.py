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

    path: Mapped[str] = mapped_column(
        index=True,
        nullable=True,
        default=None,
        comment="Materialized path technique, not implemented"
    )


    reason: Mapped[str] = mapped_column(default=None, nullable=True)
    description: Mapped[str] = mapped_column(default=None, nullable=True)
    correct_examples: Mapped[str] = mapped_column(default=None, nullable=True)
    other_info_website: Mapped[str] = mapped_column(default=None, nullable=True)
    handover_request: Mapped[datetime.datetime] = mapped_column(default=None, nullable=True)
    reasoning: Mapped[str] = mapped_column(default=None, nullable=True)

    maininfo_id: Mapped[IDType] = mapped_column(
        ForeignKey("purchases.id"),
        nullable=True,
        default=None,
        index=True,
    )

    # child items (name, quantity, price)
    subinfo = relationship(
        "PurchaseItem",
        back_populates="purchase",
        uselist=True,
        init=True,
        cascade="all, delete-orphan",
    )



class PurchaseItem(BaseModel):
    __tablename__ = "purchase_items"

    purchase_id: Mapped[IDType] = mapped_column(ForeignKey("purchases.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(default=None, nullable=True)
    quantity: Mapped[float] = mapped_column(default=1.0, nullable=False)
    price: Mapped[float] = mapped_column(default=0.0, nullable=False)

    purchase = relationship(
        "PurchaseModel",
        back_populates="subinfo",
        uselist=False,
        viewonly=False
    )
    