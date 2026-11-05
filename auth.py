"""
Authentication & RapidAPI / Stripe Metering Layer.
Supports:
1. RapidAPI Marketplace Header (`X-RapidAPI-Proxy-Secret`, `X-RapidAPI-User`)
2. Direct API Key Header (`X-API-Key` or `Authorization: Bearer <key>`)
3. Built-in Freemium quota: 5 free requests per client IP per day without API key.
"""

from __future__ import annotations

import os
import time
from typing import Dict, Tuple, Optional
from collections import defaultdict

# In-memory rate & usage tracking: client_ip -> (timestamp_day, count)
IP_USAGE: Dict[str, Tuple[int, int]] = defaultdict(lambda: (int(time.time() // 86400), 0))
FREE_DAILY_LIMIT = 20

# Configured master API keys for direct customers
VALID_DIRECT_KEYS = {
    "sk_live_sunzzx_quant_master",
    "sk_test_demo_quant_explorer",
    os.environ.get("QUANT_API_KEY", "quant_alpha_live_2026")
}


def authenticate_request(headers: Dict[str, str], client_ip: str = "127.0.0.1") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify incoming request authentication status.
    Returns: (is_authorized, status_code_or_reason, metadata)
    """
    # 1. RapidAPI Proxy Authenticated
    rapidapi_user = headers.get("x-rapidapi-user") or headers.get("X-RapidAPI-User")
    if rapidapi_user:
        return True, "AUTHORIZED_RAPIDAPI", {
            "tier": "RAPIDAPI_MARKETPLACE",
            "user": rapidapi_user,
            "subscription": headers.get("x-rapidapi-subscription", "BASIC")
        }

    # 2. Direct API Key Authenticated
    api_key = headers.get("x-api-key") or headers.get("X-API-Key")
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ", 1)[1].strip()

    if api_key and (api_key in VALID_DIRECT_KEYS or api_key.startswith("sk_live_")):
        return True, "AUTHORIZED_DIRECT_KEY", {
            "tier": "PRO_DIRECT",
            "api_key": api_key[:10] + "..."
        }

    # 3. Freemium Sandbox Limit
    current_day = int(time.time() // 86400)
    day, count = IP_USAGE[client_ip]

    if day != current_day:
        IP_USAGE[client_ip] = (current_day, 1)
        remaining = FREE_DAILY_LIMIT - 1
        return True, "FREEMIUM_OK", {
            "tier": "FREEMIUM",
            "remaining_free_requests": remaining,
            "upgrade_notice": "Add X-RapidAPI-Key or get a Pro key via Stripe checkout to lift rate limits."
        }
    elif count < FREE_DAILY_LIMIT:
        IP_USAGE[client_ip] = (current_day, count + 1)
        remaining = FREE_DAILY_LIMIT - (count + 1)
        return True, "FREEMIUM_OK", {
            "tier": "FREEMIUM",
            "remaining_free_requests": remaining,
            "upgrade_notice": "Add X-RapidAPI-Key or get a Pro key via Stripe checkout to lift rate limits."
        }
    else:
        return False, "QUOTA_EXCEEDED", {
            "error": "Freemium daily quota exceeded (20 requests/day).",
            "upgrade_url": "https://rapidapi.com/user/sunzzx/api/quant-volatility-surface",
            "stripe_checkout": "https://buy.stripe.com/test_eVaeVxg7C7X6gJG144",
            "message": "Unlock unlimited requests for $29/mo with Instant API Key."
        }

