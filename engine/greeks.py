"""
Institutional Quantitative Greeks & Analytical Derivatives Engine.
Calculates Black-Scholes-Merton option prices and full sensitivity surface (1st & 2nd order Greeks).
"""

from __future__ import annotations

import math
from typing import Dict, Any


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function (Abramowitz & Stegun approximation)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


def calculate_d1_d2(S: float, K: float, T: float, r: float, q: float, sigma: float) -> tuple[float, float]:
    """Compute d1 and d2 for Black-Scholes framework."""
    if T <= 0.0 or sigma <= 0.0:
        return 0.0, 0.0
    numerator = math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T
    denominator = sigma * math.sqrt(T)
    d1 = numerator / denominator
    d2 = d1 - denominator
    return d1, d2


def calculate_black_scholes_price(S: float, K: float, T: float, r: float, q: float, sigma: float, option_type: str = "call") -> float:
    """Calculate European option fair value."""
    if T <= 0.0:
        return max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)

    d1, d2 = calculate_d1_d2(S, K, T, r, q, sigma)
    df_r = math.exp(-r * T)
    df_q = math.exp(-q * T)

    if option_type.lower() == "call":
        return S * df_q * norm_cdf(d1) - K * df_r * norm_cdf(d2)
    else:
        return K * df_r * norm_cdf(-d2) - S * df_q * norm_cdf(-d1)


def calculate_all_greeks(S: float, K: float, T: float, r: float, q: float, sigma: float, option_type: str = "call") -> Dict[str, Any]:
    """
    Compute comprehensive 1st, 2nd, and cross-order Greeks:
    - Delta: dV/dS
    - Gamma: d^2V/dS^2
    - Vega:  dV/dsigma (per 1% vol change and per 100% vol)
    - Theta: dV/dt (per day decay)
    - Rho:   dV/dr (per 1% rate change)
    - Vanna: d^2V / (dS dsigma) (cross-gamma to volatility)
    - Volga: d^2V / dsigma^2 (convexity of vega)
    """
    is_call = (option_type.lower() == "call")
    if T <= 0.0001 or sigma <= 0.0001:
        price = max(0.0, S - K) if is_call else max(0.0, K - S)
        return {
            "price": round(price, 4),
            "delta": 1.0 if (is_call and S > K) else (-1.0 if (not is_call and S < K) else 0.0),
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
            "rho": 0.0,
            "vanna": 0.0,
            "volga": 0.0
        }

    d1, d2 = calculate_d1_d2(S, K, T, r, q, sigma)
    sqrt_T = math.sqrt(T)
    df_r = math.exp(-r * T)
    df_q = math.exp(-q * T)
    pdf_d1 = norm_pdf(d1)

    # 1. Price
    price = calculate_black_scholes_price(S, K, T, r, q, sigma, option_type)

    # 2. Delta
    if is_call:
        delta = df_q * norm_cdf(d1)
    else:
        delta = df_q * (norm_cdf(d1) - 1.0)

    # 3. Gamma
    gamma = (df_q * pdf_d1) / (S * sigma * sqrt_T)

    # 4. Vega (total dV/dsigma, and 1% point shift)
    vega_raw = S * df_q * pdf_d1 * sqrt_T
    vega_1pct = vega_raw / 100.0

    # 5. Theta (decay per calendar day, 365-day basis)
    term1 = -(S * df_q * pdf_d1 * sigma) / (2.0 * sqrt_T)
    if is_call:
        term2 = -r * K * df_r * norm_cdf(d2) + q * S * df_q * norm_cdf(d1)
    else:
        term2 = r * K * df_r * norm_cdf(-d2) - q * S * df_q * norm_cdf(-d1)
    theta_annual = term1 + term2
    theta_daily = theta_annual / 365.0

    # 6. Rho (per 1% change in risk-free interest rate)
    if is_call:
        rho_annual = K * T * df_r * norm_cdf(d2)
    else:
        rho_annual = -K * T * df_r * norm_cdf(-d2)
    rho_1pct = rho_annual / 100.0

    # 7. Vanna (sensitivity of delta to volatility or vega to spot)
    vanna = -df_q * pdf_d1 * (d2 / sigma)

    # 8. Volga / Vomma (second order sensitivity to volatility)
    volga = vega_raw * (d1 * d2 / sigma)

    return {
        "price": round(price, 4),
        "delta": round(delta, 5),
        "gamma": round(gamma, 6),
        "vega": round(vega_1pct, 5),
        "vega_raw": round(vega_raw, 4),
        "theta": round(theta_daily, 5),
        "rho": round(rho_1pct, 5),
        "vanna": round(vanna, 6),
        "volga": round(volga, 6),
        "parameters": {
            "spot": S,
            "strike": K,
            "time_to_maturity": T,
            "risk_free_rate": r,
            "dividend_yield": q,
            "volatility": sigma,
            "option_type": option_type
        }
    }

