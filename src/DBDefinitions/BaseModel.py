import uuid
import sqlalchemy
import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import MappedAsDataclass, Mapped, mapped_column

def UUIDFKey(ForeignKeyArg=None, **kwargs):
    newkwargs = {
        **kwargs,
        "index": True, 
        "primary_key": False, 
        "default": None,
        "nullable": True,
        "comment": "foreign key"
    }
    return mapped_column(**newkwargs)

def UUIDColumn(**kwargs):
    newkwargs = {
        **kwargs,
        "index": True, 
        "primary_key": True, 
        "default_factory": uuid.uuid4, 
        "comment": "primary key"
    }
    return mapped_column(**newkwargs)

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#

IDType = uuid.UUID

class BaseModel(MappedAsDataclass, DeclarativeBase):
    """Base model with audit fields and RBAC support.
    
    All entities inherit from BaseModel to get:
    - UUID primary key (id)
    - Audit timestamps (created, lastchange)
    - User tracking (createdby_id, changedby_id) - references external UG service
    - RBAC integration (rbacobject_id)
    
    Note: User IDs reference external User-Group service, no FK constraints.
    """
    
    id: Mapped[IDType] = UUIDColumn(index=True, primary_key=True, default_factory=uuid.uuid4)

    # Audit timestamps - automatically managed by database
    created: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="timestamp of creation"
    )
    
    lastchange: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        onupdate=sqlalchemy.sql.func.now(),
        comment="timestamp of last modification"
    )

    # User tracking - who created/modified this record
    # Note: User IDs reference external UG service, no FK constraint
    createdby_id: Mapped[IDType] = UUIDFKey(
        comment="user who created this entity (references external UG service)"
    )
    
    changedby_id: Mapped[IDType] = UUIDFKey(
        comment="user who last modified this entity (references external UG service)"
    )

    # RBAC integration - reference to role-based access control object
    rbacobject_id: Mapped[IDType] = UUIDFKey(
        comment="rbac object identifier for permission management"
    )
###
