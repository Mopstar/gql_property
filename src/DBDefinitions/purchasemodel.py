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
    __tablename__ = "purchases_evolution"
    path_attribute_name = "path"
    parent_attribute_name = "masterpurchase"
    parent_id_attribute_name = "maininfo_id"
    children_attribute_name = "subpurchases"

    path: Mapped[str] = mapped_column(
        index=True,
        nullable=True,
        default=None,
        comment="Materialized path technique, not implemented"
    )

    name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="Purchase request name"
    )

    reason: Mapped[str] = mapped_column(default=None, nullable=True)
    description: Mapped[str] = mapped_column(default=None, nullable=True)
    correct_examples: Mapped[str] = mapped_column(default=None, nullable=True)
    other_info_website: Mapped[str] = mapped_column(default=None, nullable=True)
    handover_request: Mapped[datetime.datetime] = mapped_column(default=None, nullable=True)
    reasoning: Mapped[str] = mapped_column(default=None, nullable=True)
    status: Mapped[str] = mapped_column(
        default="draft",
        nullable=False,
        comment="Lifecycle state of the request (draft/submitted/approved/declined/fulfilled)",
    )
    requested_delivery: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="Preferred handover date for the requested asset or service",
    )
    submitted_at: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="Timestamp when the request was formally submitted",
    )

    requester_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("users.id"),
        comment="User who created the request",
    )
    approver_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("users.id"),
        comment="User responsible for approving the request",
    )

    maininfo_id: Mapped[IDType] = mapped_column(
        ForeignKey("purchases_evolution.id"),
        nullable=True,
        default=None,
        index=True,
    )

    # Hierarchical relationship - purchases can have sub-purchases
    masterpurchase = relationship(
        "PurchaseModel",
        remote_side="PurchaseModel.id",
        foreign_keys=[maininfo_id],
        back_populates="subpurchases",
        uselist=False,
    )

    subpurchases = relationship(
        "PurchaseModel",
        foreign_keys=[maininfo_id],
        back_populates="masterpurchase",
        uselist=True,
    )

    # child items (name, quantity, price)
    subinfo = relationship(
        "PurchaseItem",
        back_populates="purchase",
        uselist=True,
        init=True,
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def is_submitted(self) -> bool:
        return self.submitted_at is not None

    @hybrid_property
    def total_cost(self) -> float:
        return sum(
            (item.price or 0.0) * (item.quantity or 0.0)
            for item in (self.subinfo or [])
        )



class PurchaseItem(BaseModel):
    __tablename__ = "purchase_items_evolution"

    # allow default None to satisfy dataclass field ordering when BaseModel defines defaulted fields
    purchase_id: Mapped[IDType] = mapped_column(
        ForeignKey("purchases_evolution.id", ondelete="CASCADE"), 
        index=True, 
        nullable=True, 
        default=None
    )

    name: Mapped[str] = mapped_column(default=None, nullable=True)
    quantity: Mapped[float] = mapped_column(default=1.0, nullable=False)
    price: Mapped[float] = mapped_column(default=0.0, nullable=False)

    purchase = relationship(
        "PurchaseModel",
        back_populates="subinfo",
        uselist=False,
        viewonly=False
    )
    
    
