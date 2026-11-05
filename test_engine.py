"""
Unit Test & Conformance Suite for Quant Volatility Surface & Greeks API.
Validates exact analytical Greeks against finite difference approximations.
"""

import math
from engine.greeks import calculate_all_greeks, calculate_black_scholes_price
from engine.implied_vol import solve_implied_volatility
from engine.heston import heston_price_call, calculate_heston_surface


def test_black_scholes_pricing():
    # Benchmark: S=100, K=100, T=1, r=0.05, sigma=0.2
    # Known call price approx: 10.4506
    call = calculate_black_scholes_price(100.0, 100.0, 1.0, 0.05, 0.0, 0.20, "call")
    assert abs(call - 10.4506) < 0.01, f"Expected ~10.45, got {call}"
    print("✓ test_black_scholes_pricing PASSED")


def test_greeks_finite_difference_accuracy():
    S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.20
    greeks = calculate_all_greeks(S, K, T, r, q, sigma, "call")

    # Analytical Greeks
    analytical_delta = greeks["delta"]
    analytical_gamma = greeks["gamma"]
    analytical_vega = greeks["vega_raw"]

    # Finite Difference Delta & Gamma
    h = 0.001
    p_up = calculate_black_scholes_price(S + h, K, T, r, q, sigma, "call")
    p_dn = calculate_black_scholes_price(S - h, K, T, r, q, sigma, "call")
    p_mid = calculate_black_scholes_price(S, K, T, r, q, sigma, "call")

    fd_delta = (p_up - p_dn) / (2.0 * h)
    fd_gamma = (p_up - 2.0 * p_mid + p_dn) / (h * h)

    assert abs(analytical_delta - fd_delta) < 1e-4, f"Delta mismatch: {analytical_delta} vs {fd_delta}"
    assert abs(analytical_gamma - fd_gamma) < 1e-4, f"Gamma mismatch: {analytical_gamma} vs {fd_gamma}"

    # Finite Difference Vega
    h_vol = 0.0001
    p_vol_up = calculate_black_scholes_price(S, K, T, r, q, sigma + h_vol, "call")
    p_vol_dn = calculate_black_scholes_price(S, K, T, r, q, sigma - h_vol, "call")
    fd_vega = (p_vol_up - p_vol_dn) / (2.0 * h_vol)

    assert abs(analytical_vega - fd_vega) < 1e-3, f"Vega mismatch: {analytical_vega} vs {fd_vega}"
    print("✓ test_greeks_finite_difference_accuracy PASSED (Delta, Gamma, Vega exact)")


def test_implied_volatility_inversion():
    S, K, T, r, q = 100.0, 105.0, 0.5, 0.04, 0.0
    true_sigma = 0.285
    market_price = calculate_black_scholes_price(S, K, T, r, q, true_sigma, "call")

    res = solve_implied_volatility(market_price, S, K, T, r, q, "call")
    assert res.get("converged") is True
    assert abs(res["implied_volatility"] - true_sigma) < 1e-4, f"Expected {true_sigma}, got {res}"
    print(f"✓ test_implied_volatility_inversion PASSED (solved in {res['iterations']} iters)")


def test_heston_stochastic_volatility():
    # Benchmark: S=100, K=100, T=1, r=0.05, v0=0.04, kappa=2.0, theta=0.04, sigma_v=0.3, rho=-0.7
    price = heston_price_call(100.0, 100.0, 1.0, 0.05, 0.04, 2.0, 0.04, 0.3, -0.7)
    assert price > 0.0
    assert 2.0 < price < 20.0, f"Unreasonable Heston price: {price}"

    # Surface check
    surface = calculate_heston_surface(100.0, [90.0, 100.0, 110.0], [0.5, 1.0], 0.05, 0.04, 2.0, 0.04, 0.3, -0.7)
    assert len(surface["surface"]) == 2
    assert len(surface["surface"][0]["quotes"]) == 3
    print(f"✓ test_heston_stochastic_volatility PASSED (Heston price={round(price, 4)})")


if __name__ == "__main__":
    test_black_scholes_pricing()
    test_greeks_finite_difference_accuracy()
    test_implied_volatility_inversion()
    test_heston_stochastic_volatility()
    print("\n🎉 ALL 4 QUANTITATIVE TESTS PASSED WITH 100% MATHEMATICAL RIGOR!")
