# 📐 Quant Volatility Surface & Institutional Derivatives Greeks API

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![RapidAPI](https://img.shields.io/badge/RapidAPI-Verified%20Provider-0052cc.svg)](https://rapidapi.com)

**High-precision, institutional-grade quantitative finance API** providing 1st, 2nd, and cross-order Black-Scholes Greeks, high-speed hybrid Newton-Raphson & Brent Implied Volatility inversion, and semi-analytical Heston Stochastic Volatility surface calibration.

Built by **Ayush Kandwal (@Sunzzx)** — AI & Quant Researcher, Dual IIT Scholar.

---

## ⚡ Key Capabilities

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health status, server telemetry, and active capability manifest |
| `/api/v1/greeks` | `GET/POST` | Exact analytical Delta, Gamma, Vega, Theta, Rho, Vanna, and Volga |
| `/api/v1/implied-volatility` | `GET/POST` | Root-finding Brent/Newton-Raphson IV solver with arbitrage bounds |
| `/api/v1/heston/price` | `GET/POST` | Semi-analytical characteristic function pricing (Gauss quadrature) |
| `/api/v1/heston/surface` | `POST` | 2D Volatility Smile & Skew surface grid generation |

---

## 🚀 Quickstart

### 1. Run Locally
```bash
python3 app.py 8088
# Server listening at http://0.0.0.0:8088
```

### 2. Query Greeks
```bash
curl "http://localhost:8088/api/v1/greeks?spot=100&strike=100&time_to_maturity=1&risk_free_rate=0.05&volatility=0.2"
```

Response:
```json
{
  "status": "success",
  "data": {
    "price": 10.4506,
    "delta": 0.63683,
    "gamma": 0.018762,
    "vega": 0.37524,
    "theta": -0.01757,
    "rho": 0.53232,
    "vanna": -0.00199,
    "volga": 0.00356
  }
}
```

### 3. Invert Implied Volatility
```bash
curl "http://localhost:8088/api/v1/implied-volatility?market_price=10.45&spot=100&strike=100&time_to_maturity=1&risk_free_rate=0.05"
```

Response:
```json
{
  "status": "success",
  "data": {
    "implied_volatility": 0.19998,
    "iterations": 3,
    "converged": true,
    "method": "Newton-Raphson"
  }
}
```

---

## 💰 RapidAPI & Monetization Tiers

- **Basic (Freemium):** 20 requests/day free (Sandbox / Academic use).
- **Pro Developer ($29/mo):** 50,000 requests/month, sub-10ms latency, priority compute.
- **Ultra / Prop Desk ($99/mo):** Unlimited requests, custom correlation parameter overrides, live WebSocket volatility streaming.

Stripe Instant API Key Checkout: `https://buy.stripe.com/test_eVaeVxg7C7X6gJG144` (Peach Disc / Ayush Kandwal)

---

## 🔬 Mathematical Formulations

### Black-Scholes Greeks Surface
$$d_1 = \frac{\ln(S/K) + (r - q + \frac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}$$
$$\Delta_{\text{call}} = e^{-qT} N(d_1), \quad \Gamma = \frac{e^{-qT} N'(d_1)}{S \sigma \sqrt{T}}, \quad \mathcal{V} = S e^{-qT} N'(d_1) \sqrt{T}$$
$$\text{Vanna} = -e^{-qT} N'(d_1) \frac{d_2}{\sigma}, \quad \text{Volga} = \mathcal{V} \frac{d_1 d_2}{\sigma}$$

### Heston Stochastic Volatility
$$dS_t = \mu S_t dt + \sqrt{v_t} S_t dW_t^S$$
$$dv_t = \kappa(\theta - v_t)dt + \sigma_v \sqrt{v_t} dW_t^v, \quad \text{Cov}(dW_t^S, dW_t^v) = \rho dt$$

---

## 📜 License
MIT License — Copyright (c) 2026 Ayush Kandwal.

