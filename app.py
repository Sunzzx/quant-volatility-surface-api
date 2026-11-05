"""
Quant Volatility Surface & Institutional Derivatives Greeks API.
Deployable as FastAPI ASGI service or standalone zero-dependency HTTP server.
"""

from __future__ import annotations

import json
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from engine.greeks import calculate_all_greeks, calculate_black_scholes_price
from engine.implied_vol import solve_implied_volatility
from engine.heston import heston_price_call, calculate_heston_surface
from auth import authenticate_request


def handle_api_route(path: str, query: Dict[str, list[str]], headers: Dict[str, str], body: Dict[str, Any], client_ip: str) -> tuple[int, Dict[str, Any]]:
    # Check Auth
    is_auth, reason, meta = authenticate_request(headers, client_ip)
    if not is_auth:
        return 429, {"status": "error", **meta}

    # Helper to extract query or body param
    def get_param(name: str, default: Any, val_type=float) -> Any:
        if name in body:
            return val_type(body[name])
        if name in query and query[name]:
            return val_type(query[name][0])
        return default

    # 1. Root / Health
    if path in ("/", "/health", "/api/v1/health"):
        return 200, {
            "status": "online",
            "service": "Quant Volatility Surface & Greeks API",
            "version": "1.0.0",
            "author": "Ayush Kandwal (@Sunzzx) // AI & Quant Researcher",
            "endpoints": [
                "/api/v1/greeks",
                "/api/v1/implied-volatility",
                "/api/v1/heston/price",
                "/api/v1/heston/surface"
            ],
            "auth_tier": meta.get("tier", "UNKNOWN"),
            "documentation": "/openapi.json"
        }

    # 2. Black-Scholes Greeks Surface
    if path == "/api/v1/greeks":
        try:
            S = get_param("spot", 100.0)
            K = get_param("strike", 100.0)
            T = get_param("time_to_maturity", 1.0)
            r = get_param("risk_free_rate", 0.05)
            q = get_param("dividend_yield", 0.0)
            sigma = get_param("volatility", 0.20)
            opt_type = str(get_param("option_type", "call", val_type=str))

            result = calculate_all_greeks(S, K, T, r, q, sigma, opt_type)
            return 200, {"status": "success", "data": result, "meta": meta}
        except Exception as e:
            return 400, {"status": "error", "message": f"Calculation error: {e}"}

    # 3. Implied Volatility Solver
    if path == "/api/v1/implied-volatility":
        try:
            market_price = get_param("market_price", 10.45)
            S = get_param("spot", 100.0)
            K = get_param("strike", 100.0)
            T = get_param("time_to_maturity", 1.0)
            r = get_param("risk_free_rate", 0.05)
            q = get_param("dividend_yield", 0.0)
            opt_type = str(get_param("option_type", "call", val_type=str))

            result = solve_implied_volatility(market_price, S, K, T, r, q, opt_type)
            return 200, {"status": "success", "data": result, "meta": meta}
        except Exception as e:
            return 400, {"status": "error", "message": f"Inversion error: {e}"}

    # 4. Heston Stochastic Volatility Single Option Pricing
    if path == "/api/v1/heston/price":
        try:
            S = get_param("spot", 100.0)
            K = get_param("strike", 100.0)
            T = get_param("time_to_maturity", 1.0)
            r = get_param("risk_free_rate", 0.05)
            v0 = get_param("v0", 0.04)
            kappa = get_param("kappa", 2.0)
            theta = get_param("theta", 0.04)
            sigma_v = get_param("vol_of_vol", 0.3)
            rho = get_param("rho", -0.7)

            call_price = heston_price_call(S, K, T, r, v0, kappa, theta, sigma_v, rho)
            return 200, {
                "status": "success",
                "data": {
                    "call_price": round(call_price, 4),
                    "spot": S,
                    "strike": K,
                    "maturity": T,
                    "v0": v0,
                    "kappa": kappa,
                    "theta": theta,
                    "vol_of_vol": sigma_v,
                    "rho": rho
                },
                "meta": meta
            }
        except Exception as e:
            return 400, {"status": "error", "message": f"Heston pricing error: {e}"}

    # 5. Heston Volatility Surface Grid
    if path == "/api/v1/heston/surface":
        try:
            S = get_param("spot", 100.0)
            strikes = body.get("strikes") or [80.0, 90.0, 100.0, 110.0, 120.0]
            maturities = body.get("maturities") or [0.25, 0.5, 1.0, 2.0]
            r = get_param("risk_free_rate", 0.05)
            v0 = get_param("v0", 0.04)
            kappa = get_param("kappa", 2.0)
            theta = get_param("theta", 0.04)
            sigma_v = get_param("vol_of_vol", 0.3)
            rho = get_param("rho", -0.7)

            surface = calculate_heston_surface(S, strikes, maturities, r, v0, kappa, theta, sigma_v, rho)
            return 200, {"status": "success", "data": surface, "meta": meta}
        except Exception as e:
            return 400, {"status": "error", "message": f"Surface generation error: {e}"}

    return 404, {"status": "error", "message": f"Endpoint '{path}' not found."}


class StandaloneRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default noisy access logs

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        headers = {k: v for k, v in self.headers.items()}
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

        status, response = handle_api_route(path, query, headers, {}, client_ip)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        headers = {k: v for k, v in self.headers.items()}
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

        content_len = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_len > 0:
            try:
                body = json.loads(self.rfile.read(content_len).decode("utf-8"))
            except Exception:
                body = {}

        status, response = handle_api_route(path, query, headers, body, client_ip)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))


def run_standalone_server(port: int = 8088):
    server = ThreadingHTTPServer(("0.0.0.0", port), StandaloneRequestHandler)
    print(f"🚀 Quant Volatility Surface & Greeks API running at http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
    run_standalone_server(port)
