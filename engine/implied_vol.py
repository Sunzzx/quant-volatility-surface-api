"""
High-Precision Implied Volatility Surface Inversion Engine.
Solves for Black-Scholes implied volatility using a robust hybrid Newton-Raphson & Brent fallback.
"""

from __future__ import annotations

import math
from typing import Dict, Any, Optional
from .greeks import calculate_black_scholes_price, calculate_d1_d2, norm_pdf


def solve_implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: str = "call",
    tol: float = 1e-6,
    max_iter: int = 100
) -> Dict[str, Any]:
    """
    Invert Black-Scholes formula to calculate implied volatility from market price.
    """
    is_call = (option_type.lower() == "call")
    df_r = math.exp(-r * T)
    df_q = math.exp(-q * T)

    # Intrinsic value bounds
    intrinsic = max(0.0, S * df_q - K * df_r) if is_call else max(0.0, K * df_r - S * df_q)
    max_price = S * df_q if is_call else K * df_r

    if market_price < intrinsic - 1e-5:
        return {
            "error": "Price violates no-arbitrage lower bound (below intrinsic value).",
            "market_price": market_price,
            "intrinsic_value": round(intrinsic, 4),
            "implied_volatility": None
        }

    if market_price > max_price + 1e-5:
        return {
            "error": "Price violates no-arbitrage upper bound.",
            "market_price": market_price,
            "upper_bound": round(max_price, 4),
            "implied_volatility": None
        }

    # Initial Brenner-Subrahmanyam approximation estimate
    sigma = math.sqrt(2.0 * math.pi / T) * (market_price / S)
    if sigma <= 0.001 or sigma > 5.0 or math.isnan(sigma):
        sigma = 0.25

    # 1. Newton-Raphson Iteration
    for i in range(max_iter):
        price = calculate_black_scholes_price(S, K, T, r, q, sigma, option_type)
        diff = price - market_price

        if abs(diff) < tol:
            return {
                "implied_volatility": round(sigma, 5),
                "iterations": i + 1,
                "converged": True,
                "method": "Newton-Raphson",
                "pricing_error": round(diff, 8)
            }

        d1, _ = calculate_d1_d2(S, K, T, r, q, sigma)
        vega = S * df_q * norm_pdf(d1) * math.sqrt(T)

        if vega < 1e-8:
            break

        sigma_new = sigma - diff / vega
        if sigma_new <= 0.0001 or sigma_new > 8.0:
            break
        sigma = sigma_new

    # 2. Brent / Bisection Fallback
    low = 0.0001
    high = 5.0

    for i in range(max_iter):
        mid = 0.5 * (low + high)
        price_mid = calculate_black_scholes_price(S, K, T, r, q, mid, option_type)
        diff = price_mid - market_price

        if abs(diff) < tol or (high - low) < tol:
            return {
                "implied_volatility": round(mid, 5),
                "iterations": i + 1,
                "converged": True,
                "method": "Bisection",
                "pricing_error": round(diff, 8)
            }

        if diff > 0:
            high = mid
        else:
            low = mid

    return {
        "implied_volatility": round(0.5 * (low + high), 5),
        "iterations": max_iter,
        "converged": False,
        "method": "Bisection (Terminated at max_iter)",
        "pricing_error": round(abs(price_mid - market_price), 6)
    }
