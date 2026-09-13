#!/usr/bin/env python3
"""AIsa Similarweb client. It holds no parameters and no prices: it reads the live contract and asks the API for cost.

  similarweb_client.py discover [--refresh]            fetch (or revalidate) the live contract; print a compact route index
  similarweb_client.py describe ROUTE                  one route: parameters, enums, defaults, limits, description
  similarweb_client.py check    ROUTE k=v ...          validate a request against the live contract (no API call)
  similarweb_client.py window                          latest complete data month (free)
  similarweb_client.py quote    ROUTE k=v ...          check, then free price estimate
  similarweb_client.py call     ROUTE k=v ... --max-usd USD [--idem KEY] [--out FILE]
                                                       check -> quote -> refuse above budget -> call capped at budget
  similarweb_client.py usage    [--days 1]             charged USD from /v1/usage

ROUTE is the contract path without the /similarweb prefix, e.g. /website/traffic-engagement.
Contract: https://aisa.one/docs/openapi/similarweb.json, cached in $AISA_SIMILARWEB_CACHE or ~/.cache/aisa-similarweb.
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

CONTRACT_URL = "https://aisa.one/docs/openapi/similarweb.json"
API = "https://api.aisa.one"
CACHE = Path(os.getenv("AISA_SIMILARWEB_CACHE") or Path.home() / ".cache" / "aisa-similarweb")


# ---------------------------------------------------------------- http
def key() -> str:
    k = os.getenv("AISA_API_KEY", "").strip()
    if not k:
        raise SystemExit("AISA_API_KEY is not set.")
    return k


def http(url: str, headers: dict | None = None, auth: bool = True, timeout: int = 90):
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Authorization", "Bearer " + key())
    for h, v in (headers or {}).items():
        req.add_header(h, str(v))
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        status, hdrs, raw = resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        status, hdrs, raw = e.code, dict(e.headers), e.read()
    try:
        body = json.loads(raw)
    except Exception:
        body = raw.decode(errors="replace")
    return status, {k.lower(): v for k, v in hdrs.items()}, body


# ---------------------------------------------------------------- contract
def load_contract(refresh: bool = False, quiet: bool = True) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    spec_f, meta_f = CACHE / "contract.json", CACHE / "contract.meta.json"
    meta = json.loads(meta_f.read_text()) if meta_f.exists() else {}
    if spec_f.exists() and not refresh and time.time() - meta.get("fetched_at", 0) < meta.get("max_age", 0):
        return json.loads(spec_f.read_text())
    headers = {"If-None-Match": meta["etag"]} if (spec_f.exists() and meta.get("etag") and not refresh) else {}
    try:
        status, hdrs, body = http(CONTRACT_URL, headers, auth=False)
    except Exception as e:
        if spec_f.exists():
            print(f"warning: contract unreachable ({e}); using cached copy", file=sys.stderr)
            return json.loads(spec_f.read_text())
        raise SystemExit(f"cannot fetch contract: {e}")
    m = re.search(r"max-age=(\d+)", hdrs.get("cache-control", ""))
    new_meta = {"etag": hdrs.get("etag", meta.get("etag")), "last_modified": hdrs.get("last-modified", meta.get("last_modified")),
                "fetched_at": time.time(), "max_age": int(m.group(1)) if m else 0}
    if status == 304 and spec_f.exists():
        meta_f.write_text(json.dumps(new_meta))
        if not quiet:
            print("contract unchanged (304)", file=sys.stderr)
        return json.loads(spec_f.read_text())
    if status != 200 or not isinstance(body, dict) or "paths" not in body:
        raise SystemExit(f"contract fetch failed: HTTP {status}")
    spec_f.write_text(json.dumps(body))
    meta_f.write_text(json.dumps(new_meta))
    if not quiet:
        print(f"contract fetched ({len(body['paths'])} routes)", file=sys.stderr)
    return body


def base_url(spec: dict) -> str:
    servers = spec.get("servers") or [{"url": API + "/apis/v1"}]
    return servers[0]["url"].rstrip("/")


def ops(spec: dict) -> dict:
    out = {}
    for path, item in spec["paths"].items():
        op = item.get("get")
        if op:
            out[re.sub(r"^/similarweb", "", path)] = (path, op)
    return out


def norm_route(route: str) -> str:
    route = "/" + route.strip("/")
    return re.sub(r"^/similarweb", "", route)


def get_op(spec: dict, route: str):
    table = ops(spec)
    r = norm_route(route)
    if r not in table:
        close = [k for k in table if r.split("/")[-1][:6] in k]
        raise SystemExit(json.dumps({"error": f"route {r} is not in the contract", "similar_routes": close or sorted(table)}, indent=2))
    return table[r]


def param_line(p: dict) -> str:
    s = p.get("schema", {})
    bits = []
    if s.get("enum"):
        bits.append("|".join(map(str, s["enum"])))
    elif s.get("type"):
        bits.append(s["type"])
    if "maximum" in s:
        bits.append(f"max {int(s['maximum']) if float(s['maximum']).is_integer() else s['maximum']}")
    if "default" in s:
        bits.append(f"default {s['default']}")
    return f"{p['name']}[{', '.join(bits)}]" if bits else p["name"]


def date_rule(op: dict) -> str:
    d = op.get("description") or ""
    m = re.search(r"(Date (?:constraint|window)[^:]*:\s*.*?\.)(?:\s|$)", d)
    return m.group(1) if m else ""


def check_request(op: dict, params: dict) -> list[str]:
    declared = {p["name"]: p for p in op.get("parameters", [])}
    problems = []
    for name, p in declared.items():
        if p.get("required") and name not in params:
            problems.append(f"missing required parameter: {param_line(p)} — {p.get('description', '')}".strip(" —"))
    for name, value in params.items():
        p = declared.get(name)
        if not p:
            problems.append(f"parameter not in contract: {name}")
            continue
        s = p.get("schema", {})
        if s.get("enum") and value not in [str(x) for x in s["enum"]]:
            problems.append(f"{name}={value} not allowed; contract allows {s['enum']}")
        if s.get("type") == "integer":
            if not re.fullmatch(r"-?\d+", value):
                problems.append(f"{name}={value} must be an integer")
            elif "maximum" in s and int(value) > s["maximum"]:
                problems.append(f"{name}={value} exceeds contract maximum {s['maximum']}")
    return problems


def validated(route: str, kv: list[str]):
    params = dict(x.split("=", 1) for x in kv)
    spec = load_contract()
    path, op = get_op(spec, route)
    problems = check_request(op, params)
    if problems:  # the cache may be stale: re-fetch once before blaming the request
        spec = load_contract(refresh=True)
        path, op = get_op(spec, route)
        problems = check_request(op, params)
    return spec, path, op, params, problems


def build_url(spec: dict, path: str, params: dict) -> str:
    return base_url(spec) + path + ("?" + urllib.parse.urlencode(params) if params else "")


# ---------------------------------------------------------------- commands
def cmd_discover(a):
    spec = load_contract(refresh=a.refresh, quiet=False)
    print(f"# {spec.get('info', {}).get('title', 'contract')} · base {base_url(spec)} · {len(spec['paths'])} routes")
    for route, (path, op) in ops(spec).items():
        ps = op.get("parameters", [])
        req = ", ".join(param_line(p) for p in ps if p.get("required"))
        opt = ", ".join(param_line(p) for p in ps if not p.get("required")) or "—"
        rule = date_rule(op)
        print(f"{route}\n  required: {req}\n  optional: {opt}" + (f"\n  dates: {rule}" if rule else ""))


def cmd_describe(a):
    spec = load_contract()
    path, op = get_op(spec, a.route)
    print(json.dumps({"route": norm_route(a.route), "url": base_url(spec) + path, "summary": op.get("summary"),
                      "description": op.get("description"),
                      "required": [{"name": p["name"], "schema": p.get("schema", {}), "description": p.get("description")} for p in op.get("parameters", []) if p.get("required")],
                      "optional": [{"name": p["name"], "schema": p.get("schema", {}), "description": p.get("description")} for p in op.get("parameters", []) if not p.get("required")]}, indent=2))


def cmd_check(a):
    spec, path, op, params, problems = validated(a.route, a.kv)
    out = {"valid": not problems, "problems": problems}
    if date_rule(op):
        out["date_rule"] = date_rule(op) + " (not checked at quote time — a real call that breaks it returns a free 400 explaining the rule)"
    print(json.dumps(out, indent=2))
    sys.exit(0 if not problems else 1)


def fill_sample(p: dict, month: str) -> str | None:
    """Sample value for a probe, derived only from the contract."""
    s, d = p.get("schema", {}), p.get("description") or ""
    if "YYYY-MM" in d:
        return month
    if s.get("enum"):
        return str(s["enum"][0])
    if "default" in s:
        return str(s["default"]).lower() if isinstance(s["default"], bool) else str(s["default"])
    m = re.search(r"e\.g\.\s*([^\s,;)]+)", d)
    if m:
        return m.group(1).rstrip(".")
    return {"integer": "1", "boolean": "true"}.get(s.get("type"))


def cmd_window(a):
    spec = load_contract()
    # the route whose description requires the latest month rejects any other month and names the allowed one
    latest = [r for r, (_, o) in ops(spec).items() if re.search(r"latest available data month|must be the latest", o.get("description") or "", re.I)]
    path, op = get_op(spec, latest[0] if latest else "/website/technologies")
    params = {}
    for p in op.get("parameters", []):
        if p.get("required"):
            v = fill_sample(p, "2000-01")
            if v is None:
                raise SystemExit(f"cannot derive a value for {p['name']} from the contract")
            params[p["name"]] = v
    status, _, body = http(build_url(spec, path, params))
    msg = body.get("meta", {}).get("error_message", "") if isinstance(body, dict) else ""
    m = re.search(r"between (\d{4}-\d{2}) and (\d{4}-\d{2})", msg)
    if not m:
        print(json.dumps({"status": status, "error": body}, indent=2))
        sys.exit(1)
    print(json.dumps({"latest_month": m.group(2), "allowed_range": [m.group(1), m.group(2)], "probed_route": norm_route(path),
                      "note": "other date rules are in each route's description (describe ROUTE)"}, indent=2))


def quote_request(url: str) -> dict:
    status, _, body = http(url, {"X-AISA-Cost-Mode": "quote"})
    micros = body.get("estimated_cost_micros_usd") if isinstance(body, dict) else None
    if status != 200 or micros is None:
        return {"ok": False, "status": status, "error": body}
    return {"ok": True, "status": 200, "usd": micros / 1e6, "may_exceed_estimate": body.get("may_exceed_estimate")}


def quoted(a):
    spec, path, op, params, problems = validated(a.route, a.kv)
    if problems:
        print(json.dumps({"valid": False, "problems": problems, "note": "fix against the live contract (describe ROUTE); nothing was sent"}, indent=2))
        sys.exit(1)
    url = build_url(spec, path, params)
    q = quote_request(url)
    if not q["ok"] and q["status"] == 400:
        spec = load_contract(refresh=True)
        path, op = get_op(spec, a.route)
        problems = check_request(op, params)
        q["note"] = ("the contract changed; re-check shows: " + "; ".join(problems)) if problems else "rejected at quote time; nothing was charged"
    return spec, path, op, params, url, q


def cmd_quote(a):
    _, _, op, _, _, q = quoted(a)
    if q["ok"] and date_rule(op):
        q["date_rule"] = date_rule(op)
    print(json.dumps(q, indent=2))
    sys.exit(0 if q["ok"] else 1)


def cmd_call(a):
    spec, path, op, params, url, q = quoted(a)
    if not q["ok"]:
        print(json.dumps(q, indent=2))
        sys.exit(1)
    if a.max_usd is None:
        print(json.dumps({"needs_budget": True, "quoted_usd": q["usd"], "may_exceed_estimate": q["may_exceed_estimate"],
                          "note": "show the user this quote; re-run with --max-usd <approved USD>"}, indent=2))
        sys.exit(3)
    if q["usd"] > a.max_usd:
        print(json.dumps({"refused": True, "quoted_usd": q["usd"], "max_usd": a.max_usd,
                          "note": "quote exceeds the approved budget; nothing was charged"}, indent=2))
        sys.exit(2)
    headers = {"X-AISA-Max-Price-USD": f"{a.max_usd:.6f}", "Idempotency-Key": a.idem or ("sw-" + uuid.uuid4().hex[:16])}
    t0 = time.time()
    status, hdrs, body = http(url, headers)
    cost = hdrs.get("x-aisa-customer-cost-micros-usd")
    out = {"status": status, "quoted_usd": q["usd"], "cost_usd": (int(cost) / 1e6) if cost else None,
           "request_id": hdrs.get("x-request-id"), "latency_s": round(time.time() - t0, 2)}
    if isinstance(body, dict):
        meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
        if status == 200:
            out["data_month"] = meta.get("last_updated") or meta.get("end_date")
        if meta.get("error_message"):
            out["note"] = "date or value rule returned by the API (not billed): " + meta["error_message"]
        err = body.get("error")
        if isinstance(err, dict) and err.get("supported"):
            out["note"] = f"{err.get('message')} — valid values: {json.dumps(err['supported'])}"
        if status == 503 and isinstance(err, dict) and err.get("retryable"):
            out["note"] = "transient 503, not billed — retry once with a new Idempotency-Key"
    out["data"] = body
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=2))
        print(json.dumps({k: v for k, v in out.items() if k != "data"}, indent=2), "-> data written to", a.out)
    else:
        print(json.dumps(out, indent=2))
    sys.exit(0 if status == 200 else 1)


def cmd_usage(a):
    end = int(time.time())
    start = end - 86400 * a.days
    status, _, body = http(f"{API}/v1/usage?start_time={start}&end_time={end}")
    if isinstance(body, dict) and "totals" in body:
        t = body["totals"]
        print(json.dumps({"days": a.days, "requests": t.get("requests"), "failed": t.get("failed_requests"),
                          "charged_usd": (t["charged_micros_usd"] / 1e6) if "charged_micros_usd" in t else None}, indent=2))
    else:
        print(json.dumps({"status": status, "body": body}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("discover"); s.add_argument("--refresh", action="store_true"); s.set_defaults(fn=cmd_discover)
    s = sub.add_parser("describe"); s.add_argument("route"); s.set_defaults(fn=cmd_describe)
    for name, fn in (("check", cmd_check), ("quote", cmd_quote)):
        s = sub.add_parser(name); s.add_argument("route"); s.add_argument("kv", nargs="*"); s.set_defaults(fn=fn)
    s = sub.add_parser("call"); s.add_argument("route"); s.add_argument("kv", nargs="*")
    s.add_argument("--max-usd", type=float, default=None, help="approved budget in USD; required to execute")
    s.add_argument("--idem", default=None); s.add_argument("--out", default=None); s.set_defaults(fn=cmd_call)
    s = sub.add_parser("window"); s.set_defaults(fn=cmd_window)
    s = sub.add_parser("usage"); s.add_argument("--days", type=int, default=1); s.set_defaults(fn=cmd_usage)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
