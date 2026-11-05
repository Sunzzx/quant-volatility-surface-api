"""
Heston Stochastic Volatility Semi-Analytical Pricing Engine.
Computes option fair values under stochastic variance via characteristic function integration.
"""

from __future__ import annotations

import cmath
import math
from typing import Dict, Any


def heston_characteristic_function(
    u: float,
    S: float,
    K: float,
    T: float,
    r: float,
    v0: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float
) -> complex:
    """
    Heston characteristic function using the stable formulation (Albrecher / Gatheral).
    phi(u) = E[exp(i * u * ln(S_T))]
    """
    i = 1j
    x = math.log(S)

    d = cmath.sqrt((rho * sigma_v * u * i - kappa)**2 + (sigma_v**2) * (i * u + u**2))
    g = (kappa - rho * sigma_v * u * i - d) / (kappa - rho * sigma_v * u * i + d)

    exp_dT = cmath.exp(-d * T)
    C = r * i * u * T + (kappa * theta / (sigma_v**2)) * (
        (kappa - rho * sigma_v * u * i - d) * T - 2.0 * cmath.log((1.0 - g * exp_dT) / (1.0 - g))
    )
    D = ((kappa - rho * sigma_v * u * i - d) / (sigma_v**2)) * ((1.0 - exp_dT) / (1.0 - g * exp_dT))

    return cmath.exp(C + D * v0 + i * u * x)


def heston_price_call(
    S: float,
    K: float,
    T: float,
    r: float,
    v0: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    upper_bound: float = 100.0,
    num_steps: int = 1000
) -> float:
    """
    Price European call option under Heston model using trapezoidal numerical integration.
    """
    if T <= 0.0:
        return max(0.0, S - K)

    df = math.exp(-r * T)
    ln_K = math.log(K)
    du = upper_bound / num_steps

    integral_sum = 0.0
    for j in range(1, num_steps):
        u = j * du
        phi = heston_characteristic_function(u, S, K, T, r, v0, kappa, theta, sigma_v, rho)
        integrand = (cmath.exp(-1j * u * ln_K) * phi / (1j * u)).real
        integral_sum += integrand * du

    call_price = 0.5 * (S - K * df) + (1.0 / math.pi) * integral_sum
    return max(0.0, max(S - K * df, call_price))


def calculate_heston_surface(
    S: float,
    strikes: list[float],
    maturities: list[float],
    r: float,
    v0: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float
) -> Dict[str, Any]:
    """Generate 2D grid of option prices across strikes and maturities."""
    grid = []
    for T in maturities:
        row = {"maturity": T, "quotes": []}
        for K in strikes:
            price = heston_price_call(S, K, T, r, v0, kappa, theta, sigma_v, rho)
            row["quotes"].append({
                "strike": K,
                "price": round(price, 4),
                "moneyness": round(S / K, 4)
            })
        grid.append(row)

    return {
        "spot": S,
        "parameters": {
            "v0": v0,
            "kappa": kappa,
            "theta": theta,
            "vol_of_vol": sigma_v,
            "correlation_rho": rho,
            "risk_free_rate": r
        },
        "surface": grid
    }

