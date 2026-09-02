import os
import logging
from app.services.razorpay.base import RazorpayProvider
from app.services.razorpay.demo_provider import DemoRazorpayProvider
from app.services.razorpay.live_provider import LiveRazorpayProvider

logger = logging.getLogger(__name__)

def get_razorpay_provider() -> RazorpayProvider:
    """
    Factory function to return the correct RazorpayProvider implementation.
    Reads RAZORPAY_MODE environment variable ('demo' or 'live').
    Fails safely if misconfigured.
    """
    mode = os.environ.get("RAZORPAY_MODE", "demo").lower()

    if mode == "demo":
        logger.info("Initializing DemoRazorpayProvider (Hackathon Mode).")
        return DemoRazorpayProvider()
    
    elif mode == "live":
        logger.info("Initializing LiveRazorpayProvider (Production Mode).")
        return LiveRazorpayProvider()
        
    else:
        raise ValueError(f"Invalid RAZORPAY_MODE: '{mode}'. Must be 'demo' or 'live'.")
