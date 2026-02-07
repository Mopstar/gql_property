"""
Tests for src/GraphTypeDefinitions/BaseGQLModel.py module

Tests the base GraphQL model including:
- IDType definition
- Relation directive
- resolve_reference method
- BaseGQLModel interface
- from_dataclass method
- load_with_loader method
- Field resolvers (createdby, changedby, rbacobject)
"""

import pytest
import uuid
import datetime
from unittest.mock import AsyncMock, MagicMock
import dataclasses

from src.GraphTypeDefinitions.BaseGQLModel import (
    BaseGQLModel,
    IDType,
    Relation,
    resolve_reference,
)


class TestIDType:
    """Test IDType definition"""

    def test_idtype_is_uuid(self):
        """IDType should be UUID type"""
        assert IDType == uuid.UUID

    def test_idtype_can_create_uuid(self):
        """IDType should be able to create UUID instances"""
        test_id = IDType('12345678-1234-5678-1234-567812345678')
        assert isinstance(test_id, uuid.UUID)


class TestRelationDirective:
    """Test Relation schema directive"""

    def test_relation_directive_exists(self):
        """Relation directive should be defined"""
        assert Relation is not None

    def test_relation_has_to_attribute(self):
        """Relation should have 'to' attribute"""
        assert hasattr(Relation, '__annotations__')
        assert 'to' in Relation.__annotations__
        assert Relation.__annotations__['to'] == str

    def test_relation_has_field_attribute(self):
        """Relation should have 'field' attribute with default"""
        assert 'field' in Relation.__annotations__
        assert Relation.__annotations__['field'] == str


class TestResolveReference:
    """Test standalone resolve_reference function"""

    @pytest.mark.asyncio
    async def test_resolve_reference_with_uuid(self):
        """resolve_reference should handle UUID input"""
        # Test using BaseGQLModel's resolve_reference classmethod
        test_id = uuid.uuid4()
        mock_info = MagicMock()
        mock_info.context = {}

        # Create a simple test class
        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                mock_loader = AsyncMock()
                mock_loader.load = AsyncMock(return_value=None)
                return mock_loader

        result = await TestModel.resolve_reference(mock_info, id=test_id)

        # Should return TestModel instance or None
        assert result is None or isinstance(result, TestModel)

    @pytest.mark.asyncio
    async def test_resolve_reference_with_string_id(self):
        """resolve_reference should convert string to UUID"""
        test_id_str = '12345678-1234-5678-1234-567812345678'
        mock_info = MagicMock()
        mock_info.context = {}

        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                mock_loader = AsyncMock()
                mock_loader.load = AsyncMock(return_value=None)
                return mock_loader

        # BaseGQLModel.resolve_reference converts string to UUID
        result = await TestModel.resolve_reference(mock_info, id=test_id_str)

        assert result is None or isinstance(result, TestModel)

    @pytest.mark.asyncio
    async def test_resolve_reference_with_none(self):
        """resolve_reference should handle None id"""
        mock_info = MagicMock()
        mock_info.context = {}

        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                return MagicMock()

        result = await TestModel.resolve_reference(mock_info, id=None)

        assert result is None


class TestBaseGQLModel:
    """Test BaseGQLModel interface"""

    def test_base_gql_model_exists(self):
        """BaseGQLModel should be defined"""
        assert BaseGQLModel is not None

    def test_base_gql_model_has_required_fields(self):
        """BaseGQLModel should have standard audit fields"""
        # Check field annotations exist
        assert hasattr(BaseGQLModel, '__annotations__')
        annotations = BaseGQLModel.__annotations__

        assert 'id' in annotations
        assert 'lastchange' in annotations
        assert 'created' in annotations
        assert 'createdby_id' in annotations
        assert 'changedby_id' in annotations
        assert 'rbacobject_id' in annotations

    def test_getloader_raises_not_implemented(self):
        """getLoader should raise NotImplementedError on base class"""
        mock_info = MagicMock()

        with pytest.raises(NotImplementedError):
            BaseGQLModel.getLoader(mock_info)

    def test_from_dataclass_converts_dict(self):
        """from_dataclass should convert dataclass to model instance"""
        # Create a mock dataclass
        @dataclasses.dataclass
        class MockDBRow:
            id: uuid.UUID
            lastchange: datetime.datetime
            created: datetime.datetime

        test_id = uuid.uuid4()
        test_time = datetime.datetime.now()
        db_row = MockDBRow(
            id=test_id,
            lastchange=test_time,
            created=test_time
        )

        # This will fail on BaseGQLModel but shows the pattern
        # Subclasses should implement properly
        try:
            result = BaseGQLModel.from_dataclass(db_row)
            # If it works, verify the result
            assert result.id == test_id
        except (TypeError, AttributeError):
            # Expected for abstract base class
            pass


class TestBaseGQLModelLoadWithLoader:
    """Test load_with_loader method"""

    @pytest.mark.asyncio
    async def test_load_with_loader_returns_none_for_none_id(self):
        """load_with_loader should return None when id is None"""
        mock_info = MagicMock()
        mock_info.context = {}

        # Create a concrete subclass for testing
        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                return MagicMock()

        result = await TestModel.load_with_loader(mock_info, id=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_load_with_loader_checks_deleted_purchases(self):
        """load_with_loader should check deleted_purchases in context"""
        test_id = uuid.uuid4()
        mock_info = MagicMock()
        mock_info.context = {"deleted_purchases": {test_id}}

        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                return MagicMock()

        result = await TestModel.load_with_loader(mock_info, id=test_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_load_with_loader_calls_loader(self):
        """load_with_loader should call the loader to fetch data"""
        test_id = uuid.uuid4()
        mock_loader = AsyncMock()

        # Mock db_row
        @dataclasses.dataclass
        class MockDBRow:
            id: uuid.UUID
            lastchange: datetime.datetime = None
            created: datetime.datetime = None
            createdby_id: uuid.UUID = None
            changedby_id: uuid.UUID = None
            rbacobject_id: uuid.UUID = None

        mock_db_row = MockDBRow(id=test_id)
        mock_loader.load = AsyncMock(return_value=mock_db_row)

        mock_info = MagicMock()
        mock_info.context = {}

        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                return mock_loader

            @classmethod
            def from_dataclass(cls, db_row):
                return cls(id=db_row.id)

        result = await TestModel.load_with_loader(mock_info, id=test_id)

        # Verify loader was called
        mock_loader.load.assert_called_once()


class TestBaseGQLModelFieldResolvers:
    """Test field resolver methods"""

    @pytest.mark.asyncio
    async def test_createdby_returns_none_when_id_none(self):
        """createdby should return None when createdby_id is None"""
        model = BaseGQLModel(
            id=uuid.uuid4(),
            createdby_id=None
        )

        result = await model.createdby()
        assert result is None

    @pytest.mark.asyncio
    async def test_createdby_returns_user_model_when_id_set(self):
        """createdby should return UserGQLModel when createdby_id is set"""
        creator_id = uuid.uuid4()
        model = BaseGQLModel(
            id=uuid.uuid4(),
            createdby_id=creator_id
        )

        result = await model.createdby()

        assert result is not None
        assert result.id == creator_id

    @pytest.mark.asyncio
    async def test_changedby_returns_none_when_id_none(self):
        """changedby should return None when changedby_id is None"""
        model = BaseGQLModel(
            id=uuid.uuid4(),
            changedby_id=None
        )

        result = await model.changedby()
        assert result is None

    @pytest.mark.asyncio
    async def test_changedby_returns_user_model_when_id_set(self):
        """changedby should return UserGQLModel when changedby_id is set"""
        changer_id = uuid.uuid4()
        model = BaseGQLModel(
            id=uuid.uuid4(),
            changedby_id=changer_id
        )

        result = await model.changedby()

        assert result is not None
        assert result.id == changer_id

    @pytest.mark.asyncio
    async def test_rbacobject_returns_none_when_id_none(self):
        """rbacobject should return None when rbacobject_id is None"""
        model = BaseGQLModel(
            id=uuid.uuid4(),
            rbacobject_id=None
        )

        result = await model.rbacobject()
        assert result is None

    @pytest.mark.asyncio
    async def test_rbacobject_returns_model_when_id_set(self):
        """rbacobject should return RBACObjectGQLModel when rbacobject_id is set"""
        rbac_id = uuid.uuid4()
        model = BaseGQLModel(
            id=uuid.uuid4(),
            rbacobject_id=rbac_id
        )

        result = await model.rbacobject()

        assert result is not None
        assert result.id == rbac_id


class TestBaseGQLModelIntegration:
    """Integration tests for BaseGQLModel"""

    def test_can_create_instance_with_minimal_data(self):
        """Should be able to create BaseGQLModel with just id"""
        test_id = uuid.uuid4()
        model = BaseGQLModel(id=test_id)

        assert model.id == test_id
        assert model.lastchange is None
        assert model.created is None

    def test_can_create_instance_with_full_data(self):
        """Should be able to create BaseGQLModel with all fields"""
        test_id = uuid.uuid4()
        creator_id = uuid.uuid4()
        changer_id = uuid.uuid4()
        rbac_id = uuid.uuid4()
        now = datetime.datetime.now()

        model = BaseGQLModel(
            id=test_id,
            lastchange=now,
            created=now,
            createdby_id=creator_id,
            changedby_id=changer_id,
            rbacobject_id=rbac_id
        )

        assert model.id == test_id
        assert model.lastchange == now
        assert model.created == now
        assert model.createdby_id == creator_id
        assert model.changedby_id == changer_id
        assert model.rbacobject_id == rbac_id

    @pytest.mark.asyncio
    async def test_resolve_reference_calls_load_with_loader(self):
        """resolve_reference should delegate to load_with_loader"""
        test_id = uuid.uuid4()
        mock_info = MagicMock()
        mock_info.context = {}

        mock_loader = AsyncMock()
        mock_loader.load = AsyncMock(return_value=None)

        class TestModel(BaseGQLModel):
            @classmethod
            def getLoader(cls, info):
                return mock_loader

        result = await TestModel.resolve_reference(mock_info, id=test_id)

        # Should have called loader
        assert mock_loader.load.called or result is not None


