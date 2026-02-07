"""
Tests for src/GraphTypeDefinitions/PurchaseItemGQLModel.py module

Tests the PurchaseItem GraphQL model including:
- PurchaseItemGQLModel type
- PurchaseItemInputFilter
- Queries (purchase_item_by_id, purchase_item_page)
- Mutations (insert, update, delete)
- Field resolvers (total_price, sensitive_msg)
- Relationships (purchase)
"""

import pytest
import uuid
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.GraphTypeDefinitions.PurchaseItemGQLModel import (
    PurchaseItemGQLModel,
    PurchaseItemInputFilter,
    PurchaseItemInsertGQLModel,
    PurchaseItemUpdateGQLModel,
    PurchaseItemQuery,
)


class TestPurchaseItemInputFilter:
    """Test PurchaseItemInputFilter"""

    def test_filter_has_required_fields(self):
        """PurchaseItemInputFilter should have filtering fields"""
        assert hasattr(PurchaseItemInputFilter, '__annotations__')
        annotations = PurchaseItemInputFilter.__annotations__

        assert 'id' in annotations
        assert 'name' in annotations
        assert 'purchase_id' in annotations
        assert 'quantity' in annotations
        assert 'price' in annotations


class TestPurchaseItemGQLModel:
    """Test PurchaseItemGQLModel type"""

    def test_purchase_item_model_exists(self):
        """PurchaseItemGQLModel should be defined"""
        assert PurchaseItemGQLModel is not None

    def test_purchase_item_has_required_fields(self):
        """PurchaseItemGQLModel should have all purchase item fields"""
        annotations = PurchaseItemGQLModel.__annotations__

        assert 'name' in annotations
        assert 'description' in annotations
        assert 'quantity' in annotations
        assert 'price' in annotations
        assert 'unit' in annotations
        assert 'purchase_id' in annotations

    def test_can_create_purchase_item_instance(self):
        """Should be able to create PurchaseItemGQLModel instance"""
        item_id = uuid.uuid4()
        purchase_id = uuid.uuid4()

        item = PurchaseItemGQLModel(
            id=item_id,
            name="Test Item",
            description="Test description",
            quantity=5.0,
            price=100.0,
            unit="pcs",
            purchase_id=purchase_id
        )

        assert item.id == item_id
        assert item.name == "Test Item"
        assert item.quantity == 5.0
        assert item.price == 100.0
        assert item.purchase_id == purchase_id

    def test_getloader_returns_correct_loader(self):
        """getLoader should return PurchaseItemModel loader"""
        mock_loaders = MagicMock()
        mock_loaders.PurchaseItemModel = MagicMock()

        mock_info = MagicMock()
        mock_info.context = {'loaders': mock_loaders}

        with patch('src.GraphTypeDefinitions.PurchaseItemGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            loader = PurchaseItemGQLModel.getLoader(mock_info)

            assert loader == mock_loaders.PurchaseItemModel


class TestPurchaseItemTotalPrice:
    """Test total_price field resolver"""

    def test_total_price_calculation(self):
        """total_price should calculate quantity × price"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=5.0,
            price=100.0
        )

        total = item.total_price()

        assert total == 500.0

    def test_total_price_with_zero_quantity(self):
        """total_price should handle zero quantity"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=0.0,
            price=100.0
        )

        total = item.total_price()

        assert total == 0.0

    def test_total_price_with_zero_price(self):
        """total_price should handle zero price"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=5.0,
            price=0.0
        )

        total = item.total_price()

        assert total == 0.0

    def test_total_price_with_none_quantity(self):
        """total_price should handle None quantity"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=None,
            price=100.0
        )

        total = item.total_price()

        assert total == 0.0

    def test_total_price_with_none_price(self):
        """total_price should handle None price"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=5.0,
            price=None
        )

        total = item.total_price()

        assert total == 0.0

    def test_total_price_with_both_none(self):
        """total_price should handle both None"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=None,
            price=None
        )

        total = item.total_price()

        assert total == 0.0

    def test_total_price_with_decimal_values(self):
        """total_price should handle decimal quantities and prices"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            quantity=2.5,
            price=99.99
        )

        total = item.total_price()

        assert abs(total - 249.975) < 0.001


class TestPurchaseItemSensitiveMsg:
    """Test sensitive_msg field resolver"""

    @pytest.mark.asyncio
    async def test_sensitive_msg_with_authenticated_user(self):
        """sensitive_msg should return message for authenticated users"""
        item = PurchaseItemGQLModel(id=uuid.uuid4())

        mock_user = {"id": uuid.uuid4(), "name": "Test User"}
        mock_info = MagicMock()

        with patch('src.GraphTypeDefinitions.PurchaseItemGQLModel.getUserFromInfo') as mock_get_user:
            mock_get_user.return_value = mock_user

            result = await item.sensitive_msg(mock_info)

            assert result == "sensitive item information"

    @pytest.mark.asyncio
    async def test_sensitive_msg_without_user(self):
        """sensitive_msg should return None for unauthenticated users"""
        item = PurchaseItemGQLModel(id=uuid.uuid4())

        mock_info = MagicMock()

        with patch('src.GraphTypeDefinitions.PurchaseItemGQLModel.getUserFromInfo') as mock_get_user:
            mock_get_user.side_effect = AttributeError("No user")

            result = await item.sensitive_msg(mock_info)

            assert result is None

    @pytest.mark.asyncio
    async def test_sensitive_msg_with_user_no_id(self):
        """sensitive_msg should return None when user has no id"""
        item = PurchaseItemGQLModel(id=uuid.uuid4())

        mock_user = {"id": None}
        mock_info = MagicMock()

        with patch('src.GraphTypeDefinitions.PurchaseItemGQLModel.getUserFromInfo') as mock_get_user:
            mock_get_user.return_value = mock_user

            result = await item.sensitive_msg(mock_info)

            assert result is None

    @pytest.mark.asyncio
    async def test_sensitive_msg_with_various_exceptions(self):
        """sensitive_msg should handle various exceptions gracefully"""
        item = PurchaseItemGQLModel(id=uuid.uuid4())
        mock_info = MagicMock()

        exceptions = [AssertionError, AttributeError, KeyError, TypeError]

        for exc_type in exceptions:
            with patch('src.GraphTypeDefinitions.PurchaseItemGQLModel.getUserFromInfo') as mock_get_user:
                mock_get_user.side_effect = exc_type("Error")

                result = await item.sensitive_msg(mock_info)

                assert result is None, f"Should return None for {exc_type.__name__}"


class TestPurchaseItemQuery:
    """Test PurchaseItemQuery interface"""

    def test_query_interface_exists(self):
        """PurchaseItemQuery interface should be defined"""
        assert PurchaseItemQuery is not None

    def test_query_has_by_id_field(self):
        """PurchaseItemQuery should have purchase_item_by_id field"""
        assert hasattr(PurchaseItemQuery, '__annotations__')
        assert 'purchase_item_by_id' in PurchaseItemQuery.__annotations__

    def test_query_has_page_field(self):
        """PurchaseItemQuery should have purchase_item_page field"""
        assert 'purchase_item_page' in PurchaseItemQuery.__annotations__


class TestPurchaseItemInsertGQLModel:
    """Test PurchaseItemInsertGQLModel input"""

    def test_insert_model_has_required_fields(self):
        """PurchaseItemInsertGQLModel should have all insert fields"""
        annotations = PurchaseItemInsertGQLModel.__annotations__

        assert 'name' in annotations
        assert 'description' in annotations
        assert 'quantity' in annotations
        assert 'price' in annotations
        assert 'unit' in annotations
        assert 'purchase_id' in annotations
        assert 'id' in annotations

    def test_insert_model_getloader(self):
        """PurchaseItemInsertGQLModel should have getLoader method"""
        assert hasattr(PurchaseItemInsertGQLModel, 'getLoader')
        assert callable(PurchaseItemInsertGQLModel.getLoader)

    def test_insert_model_getloader_returns_correct_loader(self):
        """getLoader should return PurchaseItemModel loader"""
        mock_loaders = MagicMock()
        mock_loaders.PurchaseItemModel = MagicMock()

        mock_info = MagicMock()

        with patch('src.GraphTypeDefinitions.PurchaseItemGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            loader = PurchaseItemInsertGQLModel.getLoader(mock_info)

            assert loader == mock_loaders.PurchaseItemModel


class TestPurchaseItemUpdateGQLModel:
    """Test PurchaseItemUpdateGQLModel input"""

    def test_update_model_has_required_fields(self):
        """PurchaseItemUpdateGQLModel should have id and lastchange"""
        annotations = PurchaseItemUpdateGQLModel.__annotations__

        assert 'id' in annotations
        assert 'lastchange' in annotations

    def test_can_create_update_input(self):
        """Should be able to create update input instance"""
        item_id = uuid.uuid4()
        now = datetime.datetime.now()

        update_input = PurchaseItemUpdateGQLModel(
            id=item_id,
            lastchange=now
        )

        assert update_input.id == item_id
        assert update_input.lastchange == now


class TestPurchaseItemIntegration:
    """Integration tests for PurchaseItemGQLModel"""

    def test_purchase_item_with_all_fields(self):
        """Should be able to create complete purchase item"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4(),
            name="Laptop",
            description="Dell XPS 15",
            quantity=2.0,
            price=1500.0,
            unit="pcs",
            purchase_id=uuid.uuid4(),
            created=datetime.datetime.now(),
            lastchange=datetime.datetime.now(),
            createdby_id=uuid.uuid4(),
            changedby_id=uuid.uuid4(),
            rbacobject_id=uuid.uuid4()
        )

        assert item.name == "Laptop"
        assert item.description == "Dell XPS 15"
        assert item.total_price() == 3000.0

    def test_purchase_item_minimal_data(self):
        """Should be able to create purchase item with minimal data"""
        item = PurchaseItemGQLModel(
            id=uuid.uuid4()
        )

        assert item.id is not None
        assert item.name is None
        assert item.quantity is None
        assert item.price is None
        assert item.total_price() == 0.0

    def test_purchase_item_calculation_edge_cases(self):
        """Test edge cases in price calculations"""
        test_cases = [
            (0, 0, 0.0),
            (1, 1, 1.0),
            (0.5, 100, 50.0),
            (100, 0.01, 1.0),
            (None, 100, 0.0),
            (100, None, 0.0),
        ]

        for quantity, price, expected in test_cases:
            item = PurchaseItemGQLModel(
                id=uuid.uuid4(),
                quantity=quantity,
                price=price
            )
            result = item.total_price()
            assert result == expected, f"Failed for quantity={quantity}, price={price}"


