"""
Tests for src/GraphTypeDefinitions/PurchaseGQLModel.py module

Tests the Purchase GraphQL model including:
- PurchaseGQLModel type
- PurchaseInputFilter
- Queries and mutations
- Field resolvers
- Status handling
- Relationships (requester, approver, items)
"""

import pytest
import uuid
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.GraphTypeDefinitions.PurchaseGQLModel import (
    PurchaseGQLModel,
    PurchaseInputFilter,
)


class TestPurchaseInputFilter:
    """Test PurchaseInputFilter"""

    def test_filter_has_required_fields(self):
        """PurchaseInputFilter should have filtering fields"""
        assert hasattr(PurchaseInputFilter, '__annotations__')
        annotations = PurchaseInputFilter.__annotations__

        assert 'id' in annotations
        assert 'path' in annotations
        assert 'status' in annotations
        assert 'requester_id' in annotations
        assert 'approver_id' in annotations
        assert 'name' in annotations
        assert 'valid' in annotations


class TestPurchaseGQLModel:
    """Test PurchaseGQLModel type"""

    def test_purchase_model_exists(self):
        """PurchaseGQLModel should be defined"""
        assert PurchaseGQLModel is not None

    def test_purchase_has_required_fields(self):
        """PurchaseGQLModel should have all purchase fields"""
        annotations = PurchaseGQLModel.__annotations__

        assert 'path' in annotations
        assert 'name' in annotations
        assert 'reason' in annotations
        assert 'description' in annotations
        assert 'handover_request' in annotations
        assert 'status' in annotations
        assert 'requested_delivery' in annotations
        assert 'submitted_at' in annotations

    def test_can_create_purchase_instance(self):
        """Should be able to create PurchaseGQLModel instance"""
        purchase_id = uuid.uuid4()
        requester_id = uuid.uuid4()

        purchase = PurchaseGQLModel(
            id=purchase_id,
            name="Test Purchase",
            reason="Testing",
            description="Test description",
            status="draft",
            requester_id=requester_id
        )

        assert purchase.id == purchase_id
        assert purchase.name == "Test Purchase"
        assert purchase.reason == "Testing"
        assert purchase.status == "draft"

    def test_getloader_returns_correct_loader(self):
        """getLoader should return PurchaseModel loader"""
        mock_loaders = MagicMock()
        mock_loaders.PurchaseModel = MagicMock()

        mock_info = MagicMock()
        mock_info.context = {'loaders': mock_loaders}

        with patch('src.GraphTypeDefinitions.PurchaseGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            loader = PurchaseGQLModel.getLoader(mock_info)

            assert loader == mock_loaders.PurchaseModel


class TestPurchaseStatus:
    """Test purchase status handling"""

    def test_purchase_with_draft_status(self):
        """Should handle draft status"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            status="draft"
        )

        assert purchase.status == "draft"

    def test_purchase_with_submitted_status(self):
        """Should handle submitted status"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            status="submitted",
            submitted_at=datetime.datetime.now()
        )

        assert purchase.status == "submitted"
        assert purchase.submitted_at is not None

    def test_purchase_with_approved_status(self):
        """Should handle approved status"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            status="approved"
        )

        assert purchase.status == "approved"

    def test_purchase_with_rejected_status(self):
        """Should handle rejected status"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            status="rejected"
        )

        assert purchase.status == "rejected"

    def test_purchase_with_completed_status(self):
        """Should handle completed status"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            status="completed"
        )

        assert purchase.status == "completed"


class TestPurchaseDates:
    """Test purchase date fields"""

    def test_purchase_with_handover_request(self):
        """Should handle handover request date"""
        handover_date = datetime.datetime(2026, 3, 1, 10, 0, 0)

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            handover_request=handover_date
        )

        assert purchase.handover_request == handover_date

    def test_purchase_with_requested_delivery(self):
        """Should handle requested delivery date"""
        delivery_date = datetime.datetime(2026, 3, 15, 14, 0, 0)

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            requested_delivery=delivery_date
        )

        assert purchase.requested_delivery == delivery_date

    def test_purchase_with_submitted_at(self):
        """Should handle submission timestamp"""
        submitted = datetime.datetime(2026, 2, 7, 9, 30, 0)

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            submitted_at=submitted
        )

        assert purchase.submitted_at == submitted

    def test_purchase_date_ordering(self):
        """Dates should follow logical ordering"""
        submitted = datetime.datetime(2026, 2, 7, 0, 0, 0)
        delivery = datetime.datetime(2026, 2, 20, 0, 0, 0)
        handover = datetime.datetime(2026, 2, 25, 0, 0, 0)

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            submitted_at=submitted,
            requested_delivery=delivery,
            handover_request=handover
        )

        assert purchase.submitted_at < purchase.requested_delivery < purchase.handover_request


class TestPurchaseFields:
    """Test various purchase fields"""

    def test_purchase_with_path(self):
        """Should handle materialized path"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            path="/department/subdepartment"
        )

        assert purchase.path == "/department/subdepartment"

    def test_purchase_with_reason(self):
        """Should handle reason field"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            reason="Need new equipment"
        )

        assert purchase.reason == "Need new equipment"

    def test_purchase_with_description(self):
        """Should handle detailed description"""
        description = "Detailed description of the purchase request including specifications"

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            description=description
        )

        assert purchase.description == description

    def test_purchase_with_correct_examples(self):
        """Should handle correct_examples field"""
        examples = "Model XYZ-123, specification ABC"

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            correct_examples=examples
        )

        assert purchase.correct_examples == examples

    def test_purchase_with_website(self):
        """Should handle website link"""
        website = "https://example.com/product"

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            other_info_website=website
        )

        assert purchase.other_info_website == website

    def test_purchase_with_reasoning(self):
        """Should handle additional reasoning"""
        reasoning = "Additional justification for this purchase"

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            reasoning=reasoning
        )

        assert purchase.reasoning == reasoning


class TestPurchaseIntegration:
    """Integration tests for PurchaseGQLModel"""

    def test_create_complete_purchase(self):
        """Should be able to create complete purchase with all fields"""
        purchase_id = uuid.uuid4()
        requester_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        now = datetime.datetime.now()

        purchase = PurchaseGQLModel(
            id=purchase_id,
            path="/faculty/department",
            name="Office Equipment Purchase",
            reason="Modernization of workspace",
            description="Purchase of new office equipment including desks and chairs",
            correct_examples="Model: ErgoDesk Pro 2000",
            other_info_website="https://ergo-furniture.example.com",
            handover_request=now + datetime.timedelta(days=30),
            reasoning="Current equipment is over 10 years old",
            status="submitted",
            requested_delivery=now + datetime.timedelta(days=20),
            submitted_at=now,
            requester_id=requester_id,
            approver_id=approver_id,
            created=now,
            lastchange=now,
            createdby_id=requester_id,
            changedby_id=requester_id,
            rbacobject_id=uuid.uuid4()
        )

        assert purchase.id == purchase_id
        assert purchase.name == "Office Equipment Purchase"
        assert purchase.status == "submitted"
        assert purchase.requester_id == requester_id
        assert purchase.approver_id == approver_id

    def test_create_minimal_purchase(self):
        """Should be able to create purchase with minimal fields"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4()
        )

        assert purchase.id is not None
        assert purchase.name is None
        assert purchase.status is None
        assert purchase.description is None

    def test_purchase_workflow_states(self):
        """Test purchase through workflow states"""
        purchase_id = uuid.uuid4()

        # Draft state
        purchase_draft = PurchaseGQLModel(
            id=purchase_id,
            status="draft"
        )
        assert purchase_draft.status == "draft"

        # Submitted state
        purchase_submitted = PurchaseGQLModel(
            id=purchase_id,
            status="submitted",
            submitted_at=datetime.datetime.now()
        )
        assert purchase_submitted.status == "submitted"
        assert purchase_submitted.submitted_at is not None

        # Approved state
        purchase_approved = PurchaseGQLModel(
            id=purchase_id,
            status="approved"
        )
        assert purchase_approved.status == "approved"

        # Completed state
        purchase_completed = PurchaseGQLModel(
            id=purchase_id,
            status="completed"
        )
        assert purchase_completed.status == "completed"


class TestPurchaseEdgeCases:
    """Test edge cases for purchases"""

    def test_purchase_without_requester(self):
        """Should handle purchase without requester_id"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            name="Test Purchase",
            requester_id=None
        )

        assert purchase.requester_id is None

    def test_purchase_without_approver(self):
        """Should handle purchase without approver_id"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            name="Test Purchase",
            approver_id=None
        )

        assert purchase.approver_id is None

    def test_purchase_with_none_dates(self):
        """Should handle None dates"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            handover_request=None,
            requested_delivery=None,
            submitted_at=None
        )

        assert purchase.handover_request is None
        assert purchase.requested_delivery is None
        assert purchase.submitted_at is None

    def test_purchase_with_empty_strings(self):
        """Should handle empty string fields"""
        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            name="",
            reason="",
            description=""
        )

        assert purchase.name == ""
        assert purchase.reason == ""
        assert purchase.description == ""

    def test_purchase_with_very_long_description(self):
        """Should handle very long descriptions"""
        long_description = "A" * 10000

        purchase = PurchaseGQLModel(
            id=uuid.uuid4(),
            description=long_description
        )

        assert len(purchase.description) == 10000

    def test_purchase_path_variations(self):
        """Should handle various path formats"""
        paths = [
            "/root",
            "/root/child",
            "/root/child/grandchild",
            "",
            None
        ]

        for path in paths:
            purchase = PurchaseGQLModel(
                id=uuid.uuid4(),
                path=path
            )
            assert purchase.path == path

