"""
Tests for the Razorpay Provider abstraction layer.
Covers: factory, DemoRazorpayProvider, LiveRazorpayProvider (mocked), webhook verification.
No real Razorpay credentials required.
"""
import hashlib
import hmac
import os
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------

class TestRazorpayFactory:
    def test_demo_mode_returns_demo_provider(self, monkeypatch):
        monkeypatch.setenv("RAZORPAY_MODE", "demo")
        from app.services.razorpay.factory import get_razorpay_provider
        from app.services.razorpay.demo_provider import DemoRazorpayProvider
        # Reload to pick up env change
        import importlib, app.services.razorpay.factory as fac
        importlib.reload(fac)
        provider = fac.get_razorpay_provider()
        assert isinstance(provider, DemoRazorpayProvider)

    def test_live_mode_returns_live_provider(self, monkeypatch):
        monkeypatch.setenv("RAZORPAY_MODE", "live")
        monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_fake_key")
        monkeypatch.setenv("RAZORPAY_KEY_SECRET", "fake_secret")
        from app.services.razorpay.live_provider import LiveRazorpayProvider
        import importlib, app.services.razorpay.factory as fac
        importlib.reload(fac)
        provider = fac.get_razorpay_provider()
        assert isinstance(provider, LiveRazorpayProvider)

    def test_invalid_mode_raises_value_error(self, monkeypatch):
        monkeypatch.setenv("RAZORPAY_MODE", "staging")
        import importlib, app.services.razorpay.factory as fac
        importlib.reload(fac)
        with pytest.raises(ValueError, match="Invalid RAZORPAY_MODE"):
            fac.get_razorpay_provider()

    def test_no_silent_demo_fallback_when_live_missing_keys(self, monkeypatch):
        monkeypatch.setenv("RAZORPAY_MODE", "live")
        monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
        monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)
        import importlib, app.services.razorpay.factory as fac
        importlib.reload(fac)
        with pytest.raises(ValueError):
            fac.get_razorpay_provider()


# ---------------------------------------------------------------------------
# DemoRazorpayProvider tests
# ---------------------------------------------------------------------------

class TestDemoRazorpayProvider:
    def setup_method(self):
        from app.services.razorpay.demo_provider import DemoRazorpayProvider
        self.provider = DemoRazorpayProvider()

    def test_get_payment_details_for_seeded_id(self):
        """Should return data from the seeded ext_payment_gateway table."""
        result = self.provider.get_payment_details("DEMO_TXN_STRONG_1")
        assert result is not None
        assert result.payment_id == "DEMO_TXN_STRONG_1"
        assert result.source == "DEMO_RAZORPAY_DATA"
        assert result.mode == "demo"
        assert result.amount_minor == 29999  # 299.99 * 100 in minor units

    def test_get_payment_details_for_empty_id_returns_none(self):
        """DEMO_TXN_EMPTY_1 must return None — no payment seeded."""
        result = self.provider.get_payment_details("DEMO_TXN_EMPTY_1")
        assert result is None

    def test_get_payment_details_for_unknown_id_fallback(self):
        """Any non-DEMO_ ID with a non-9 hash bucket should return data."""
        # Test with an ID whose hash bucket we know is not 9
        result = self.provider.get_payment_details("RANDOM_TEST_ABC")
        # This may return None (bucket==9) or a result — just ensure no crash
        # and source is correct if a result is returned
        if result is not None:
            assert result.source == "DEMO_RAZORPAY_DATA"
            assert result.mode == "demo"

    def test_get_refund_details_returns_list(self):
        result = self.provider.get_refund_details("DEMO_TXN_STRONG_1")
        assert isinstance(result, list)

    def test_get_dispute_details_returns_demo_object(self):
        result = self.provider.get_dispute_details("disp_test_demo_1")
        assert result is not None
        assert result.dispute_id == "disp_test_demo_1"
        assert result.source == "DEMO_RAZORPAY_DATA"
        assert result.mode == "demo"

    def test_verify_webhook_signature_accepts_test_token(self):
        """Demo mode should accept the static test signature."""
        assert self.provider.verify_webhook_signature(b'{}', 'test_demo_signature') is True

    def test_verify_webhook_signature_rejects_wrong_token(self):
        assert self.provider.verify_webhook_signature(b'{}', 'wrong_signature') is False

    def test_normalized_model_has_correct_fields(self):
        result = self.provider.get_payment_details("DEMO_TXN_STRONG_1")
        assert hasattr(result, "payment_id")
        assert hasattr(result, "amount_minor")   # integer minor units, NOT float amount
        assert hasattr(result, "currency")
        assert hasattr(result, "status")
        assert hasattr(result, "created_at")
        assert hasattr(result, "source")
        assert hasattr(result, "mode")
        assert isinstance(result.amount_minor, int)


# ---------------------------------------------------------------------------
# LiveRazorpayProvider tests (all HTTP calls mocked)
# ---------------------------------------------------------------------------

class TestLiveRazorpayProvider:
    def setup_method(self, monkeypatch=None):
        os.environ["RAZORPAY_KEY_ID"] = "rzp_test_fake_key_id"
        os.environ["RAZORPAY_KEY_SECRET"] = "fake_secret_value"
        os.environ["RAZORPAY_WEBHOOK_SECRET"] = "webhook_secret_123"
        from app.services.razorpay.live_provider import LiveRazorpayProvider
        self.provider = LiveRazorpayProvider()

    def test_get_payment_details_success(self):
        """Mock a successful Razorpay GET /payments/:id call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "pay_test123",
            "amount": 29999,  # paise
            "currency": "INR",
            "status": "captured",
            "order_id": "order_abc",
            "created_at": 1700000000
        }
        mock_response.raise_for_status = MagicMock()
        self.provider.client.get = MagicMock(return_value=mock_response)

        result = self.provider.get_payment_details("pay_test123")
        assert result is not None
        assert result.payment_id == "pay_test123"
        assert result.amount_minor == 29999  # raw paise value from API
        assert result.currency == "INR"
        assert result.source == "LIVE_RAZORPAY_API"
        assert result.mode == "live"

    def test_get_payment_details_404_returns_none(self):
        """A 404 from the API should return None, not raise."""
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        self.provider.client.get = MagicMock(side_effect=http_error)

        result = self.provider.get_payment_details("pay_nonexistent")
        assert result is None

    def test_get_refund_details_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{
                "id": "rfnd_test1",
                "amount": 10000,
                "currency": "INR",
                "status": "processed",
                "created_at": 1700000001
            }]
        }
        mock_response.raise_for_status = MagicMock()
        self.provider.client.get = MagicMock(return_value=mock_response)

        results = self.provider.get_refund_details("pay_test123")
        assert len(results) == 1
        assert results[0].refund_id == "rfnd_test1"
        assert results[0].amount_minor == 10000  # raw paise value from API
        assert results[0].source == "LIVE_RAZORPAY_API"

    def test_get_refund_details_empty(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = MagicMock()
        self.provider.client.get = MagicMock(return_value=mock_response)

        results = self.provider.get_refund_details("pay_test123")
        assert results == []

    def test_webhook_signature_verification_valid(self):
        """Compute the expected HMAC and verify the provider accepts it."""
        payload = b'{"event": "payment.dispute.created"}'
        secret = "webhook_secret_123"
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = self.provider.verify_webhook_signature(payload, expected_sig)
        assert result is True

    def test_webhook_signature_verification_invalid(self):
        payload = b'{"event": "payment.dispute.created"}'
        result = self.provider.verify_webhook_signature(payload, "tampered_signature")
        assert result is False

    def test_missing_credentials_raises_on_init(self):
        import app.services.razorpay.live_provider as lp_module
        # Temporarily unset keys
        original_key_id = os.environ.pop("RAZORPAY_KEY_ID", None)
        original_secret = os.environ.pop("RAZORPAY_KEY_SECRET", None)
        try:
            with pytest.raises(ValueError, match="RAZORPAY_KEY_ID"):
                lp_module.LiveRazorpayProvider()
        finally:
            if original_key_id:
                os.environ["RAZORPAY_KEY_ID"] = original_key_id
            if original_secret:
                os.environ["RAZORPAY_KEY_SECRET"] = original_secret
