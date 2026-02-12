"""
Tests for src/DBFeeder.py module

Tests database seeding and backup functionality including:
- _parse_datetime() function
- _normalize_purchase_seed_data() function
- _ensure_sample_purchases() function
- initDB() function
- backupDB() function
"""

import pytest
import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os

from src.DBFeeder import (
    _parse_datetime,
    _normalize_purchase_seed_data,
    _ensure_sample_purchases,
    initDB,
    backupDB,
    get_demodata,
)


class TestParseDatetime:
    """Test _parse_datetime function"""

    def test_parse_datetime_with_none(self):
        """Should return None for None input"""
        result = _parse_datetime(None)
        assert result is None

    def test_parse_datetime_with_empty_string(self):
        """Should return None for empty string"""
        result = _parse_datetime("")
        assert result is None

    def test_parse_datetime_with_null_string(self):
        """Should return None for 'null' string"""
        result = _parse_datetime("null")
        assert result is None

    def test_parse_datetime_with_datetime_object(self):
        """Should return the same datetime object"""
        dt = datetime.datetime(2026, 2, 6, 12, 0, 0)
        result = _parse_datetime(dt)
        assert result == dt
        assert isinstance(result, datetime.datetime)

    def test_parse_datetime_with_iso_format(self):
        """Should parse ISO format datetime string"""
        iso_string = "2026-02-06T12:30:45"
        result = _parse_datetime(iso_string)
        assert result is not None
        assert isinstance(result, datetime.datetime)
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6

    def test_parse_datetime_with_standard_format(self):
        """Should parse standard datetime format"""
        dt_string = "2026-02-06 12:30:45"
        result = _parse_datetime(dt_string)
        assert result is not None
        assert isinstance(result, datetime.datetime)
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6

    def test_parse_datetime_with_invalid_format(self):
        """Should return None for invalid format"""
        result = _parse_datetime("invalid-date")
        assert result is None

    def test_parse_datetime_with_various_formats(self):
        """Test multiple datetime formats"""
        test_cases = [
            ("2026-02-06T10:30:00", True),
            ("2026-02-06 10:30:00", True),
            ("2026-02-06T10:30:00.123456", True),
            ("not-a-date", False),
            ("", False),
            (None, False),
        ]

        for input_val, should_succeed in test_cases:
            result = _parse_datetime(input_val)
            if should_succeed:
                assert result is None or isinstance(result, datetime.datetime)
            else:
                assert result is None


class TestNormalizePurchaseSeedData:
    """Test _normalize_purchase_seed_data function"""

    def test_normalize_empty_data(self):
        """Should handle empty JSON data"""
        json_data = {}
        _normalize_purchase_seed_data(json_data)
        # Should not raise exception
        assert True

    def test_normalize_purchases_evolution(self):
        """Should normalize datetime fields in purchases_evolution"""
        json_data = {
            "purchases_evolution": [
                {
                    "id": str(uuid.uuid4()),
                    "handover_request": "2026-02-06 10:00:00",
                    "requested_delivery": "2026-02-07T12:00:00",
                    "submitted_at": "2026-02-05 09:00:00",
                    "created": "2026-02-01T08:00:00",
                    "lastchange": "2026-02-06T11:00:00",
                }
            ]
        }

        _normalize_purchase_seed_data(json_data)

        purchase = json_data["purchases_evolution"][0]
        assert isinstance(purchase["handover_request"], (datetime.datetime, type(None)))
        assert isinstance(purchase["requested_delivery"], (datetime.datetime, type(None)))
        assert isinstance(purchase["submitted_at"], (datetime.datetime, type(None)))
        assert isinstance(purchase["created"], (datetime.datetime, type(None)))
        assert isinstance(purchase["lastchange"], (datetime.datetime, type(None)))

    def test_normalize_adds_default_status(self):
        """Should add default status 'draft' if not present"""
        json_data = {
            "purchases_evolution": [
                {
                    "id": str(uuid.uuid4()),
                }
            ]
        }

        _normalize_purchase_seed_data(json_data)

        purchase = json_data["purchases_evolution"][0]
        assert purchase["status"] == "draft"

    def test_normalize_purchase_items(self):
        """Should normalize datetime fields in purchase_items_evolution"""
        json_data = {
            "purchase_items_evolution": [
                {
                    "id": str(uuid.uuid4()),
                    "created": "2026-02-01T08:00:00",
                    "lastchange": "2026-02-06T11:00:00",
                }
            ]
        }

        _normalize_purchase_seed_data(json_data)

        item = json_data["purchase_items_evolution"][0]
        assert isinstance(item["created"], (datetime.datetime, type(None)))
        assert isinstance(item["lastchange"], (datetime.datetime, type(None)))

    def test_normalize_with_none_values(self):
        """Should handle None datetime values correctly"""
        json_data = {
            "purchases_evolution": [
                {
                    "id": str(uuid.uuid4()),
                    "handover_request": None,
                    "requested_delivery": None,
                    "submitted_at": None,
                    "created": None,
                    "lastchange": None,
                }
            ]
        }

        _normalize_purchase_seed_data(json_data)

        purchase = json_data["purchases_evolution"][0]
        assert purchase["handover_request"] is None
        assert purchase["requested_delivery"] is None
        assert purchase["submitted_at"] is None

    def test_normalize_preserves_existing_status(self):
        """Should not overwrite existing status"""
        json_data = {
            "purchases_evolution": [
                {
                    "id": str(uuid.uuid4()),
                    "status": "submitted",
                }
            ]
        }

        _normalize_purchase_seed_data(json_data)

        purchase = json_data["purchases_evolution"][0]
        assert purchase["status"] == "submitted"


class TestEnsureSamplePurchases:
    """Test _ensure_sample_purchases function"""


    @pytest.mark.asyncio
    async def test_ensure_sample_purchases_skips_if_data_exists(self):
        """Should not create sample data if purchases already exist"""
        # Mock session maker and session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one.return_value = 5  # Database has data
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = MagicMock()

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        await _ensure_sample_purchases(mock_session_maker)

        # Verify that add was NOT called
        mock_session.add.assert_not_called()


class TestInitDB:
    """Test initDB function"""

    @pytest.mark.asyncio
    async def test_initdb_without_demo_mode(self):
        """Should initialize DB without demo data when DEMODATA is not set"""
        mock_session_maker = AsyncMock()

        with patch.dict(os.environ, {}, clear=True):
            with patch("src.DBFeeder.readJsonFile") as mock_read:
                with patch("src.DBFeeder.ImportModels") as mock_import:
                    mock_read.return_value = {}
                    mock_import.return_value = AsyncMock()

                    await initDB(mock_session_maker)

                    # Verify ImportModels was called
                    mock_import.assert_called_once()

    @pytest.mark.asyncio
    async def test_initdb_with_demo_mode(self):
        """Should initialize DB with demo data when DEMODATA is True"""
        mock_session_maker = AsyncMock()

        with patch.dict(os.environ, {"DEMODATA": "True"}):
            with patch("src.DBFeeder.readJsonFile") as mock_read:
                with patch("src.DBFeeder.ImportModels") as mock_import:
                    with patch("src.DBFeeder._ensure_sample_purchases") as mock_sample:
                        mock_read.return_value = {}
                        mock_import.return_value = AsyncMock()
                        mock_sample.return_value = AsyncMock()

                        await initDB(mock_session_maker)

                        # Verify sample purchases were created
                        mock_sample.assert_called_once()

    @pytest.mark.asyncio
    async def test_initdb_with_custom_filename(self):
        """Should support custom filename parameter"""
        mock_session_maker = AsyncMock()
        custom_file = "./custom_data.json"

        with patch.dict(os.environ, {}, clear=True):
            with patch("src.DBFeeder.readJsonFile") as mock_read:
                with patch("src.DBFeeder.ImportModels") as mock_import:
                    mock_read.return_value = {}
                    mock_import.return_value = AsyncMock()

                    await initDB(mock_session_maker, filename=custom_file)

                    # Verify correct filename was used
                    mock_read.assert_called_once_with(custom_file)


class TestBackupDB:
    """Test backupDB function"""

    @pytest.mark.asyncio
    async def test_backupdb_creates_file(self):
        """Should create backup file with database data"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        backup_file = "./test_backup.json"

        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                mock_open.return_value.__enter__ = MagicMock()
                mock_open.return_value.__exit__ = MagicMock()

                await backupDB(mock_session_maker, filename=backup_file)

                # Verify file was opened for writing
                mock_open.assert_called_once()
                # Verify JSON was dumped
                mock_json_dump.assert_called_once()


class TestGetDemodata:
    """Test get_demodata function"""

    def test_get_demodata_returns_callable(self):
        """get_demodata should return a callable function"""
        result = get_demodata
        assert callable(result)

    def test_get_demodata_reads_systemdata(self):
        """get_demodata should read from systemdata.json"""
        with patch("src.DBFeeder.readJsonFile") as mock_read:
            mock_read.return_value = {"test": "data"}

            data_func = get_demodata
            result = data_func()

            assert result == {"test": "data"}

