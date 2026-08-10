"""
Mock third-party payment gateway integration.

In production this would call a real provider (Stripe/Razorpay/etc).
For this simulation, it hits a mock endpoint and demonstrates the
exception handling + logging pattern expected of a real integration.
"""
import logging

import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

MOCK_PAYMENT_GATEWAY_URL = "https://httpbin.org/post"  # stand-in mock endpoint
REQUEST_TIMEOUT_SECONDS = 5


class PaymentGatewayError(Exception):
    """Raised when the mock payment gateway call fails or times out."""


def verify_payment_intent(booking_id: int, amount: str) -> dict:
    """
    Calls the mock payment gateway to verify/simulate a payment intent.
    Returns the gateway's JSON response on success.
    Raises PaymentGatewayError on network failure or bad response.
    """
    payload = {"booking_id": booking_id, "amount": amount}

    try:
        response = requests.post(
            MOCK_PAYMENT_GATEWAY_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        logger.info("Payment gateway call succeeded for booking_id=%s", booking_id)
        return response.json()

    except Timeout as exc:
        logger.error("Payment gateway timed out for booking_id=%s", booking_id)
        raise PaymentGatewayError("Payment gateway request timed out.") from exc

    except RequestException as exc:
        logger.error(
            "Payment gateway call failed for booking_id=%s: %s", booking_id, exc
        )
        raise PaymentGatewayError(f"Payment gateway call failed: {exc}") from exc