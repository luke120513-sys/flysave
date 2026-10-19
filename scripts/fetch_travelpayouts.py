#!/usr/bin/env python3
"""Fetch supplementary Travelpayouts prices for routes already in deals.json.

The token is read from TRAVELPAYOUTS_TOKEN and sent only as the X-Access-Token
header. It is never printed. On a missing token or an API failure the existing
tp_prices.json is left untouched.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS = os.path.join(ROOT, "deals.json")
OUT = os.path.join(ROOT, "tp_prices.json")
API = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
TPE = timezone(timedelta(hours=8))
IATA = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def log(msg):
    print(msg, file=sys.stderr)


def iata(v):
    s = str(v or "").strip().upper()
    return s if len(s) == 3 and set(s) <= IATA else ""


def load_json(path, fallback):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return fallback


def collect_routes(deals):
    """TPE (and KHH, the other origin the site shows) to destinations in deals.json."""
    routes = []
    seen = set()
    for key in ("long", "custom", "longhaul", "notify", "reqConn"):
        for item in deals.get(key) or []:
            if not isinstance(item, dict):
                continue
            origin = iata(item.get("origin"))
            dest = iata(item.get("code"))
            if origin not in ("TPE", "KHH") or not dest or origin == dest:
                continue
            pair = (origin, dest)
            if pair in seen:
                continue
            seen.add(pair)
            routes.append(pair)
    routes.sort()
    return routes


def months_ahead(n=2):
    now = datetime.now(TPE)
    y, m = now.year, now.month
    out = []
    for _ in range(n):
        out.append("%04d-%02d" % (y, m))
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def day_of(value):
    s = str(value or "")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return ""


def offers_from_payload(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        data = list(data.values())
    if not isinstance(data, list):
        return []
    best = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        date = day_of(row.get("departure_at") or row.get("depart_date"))
        price = row.get("price", row.get("value"))
        try:
            price = int(round(float(price)))
        except (TypeError, ValueError):
            continue
        if not date or price <= 0:
            continue
        transfers = row.get("transfers", row.get("number_of_changes"))
        try:
            transfers = int(transfers)
        except (TypeError, ValueError):
            transfers = 0
        offer = {
            "date": date,
            "price_twd": price,
            "airline": str(row.get("airline") or row.get("gate") or "").strip().upper()[:8],
            "transfers": max(0, transfers),
            "found_at": str(row.get("found_at") or ""),
        }
        ret = day_of(row.get("return_at") or row.get("return_date"))
        if ret:
            offer["return_date"] = ret
        prev = best.get(date)
        if prev is None or price < prev["price_twd"]:
            best[date] = offer
    return [best[k] for k in sorted(best)]


class TokenRejected(Exception):
    pass


def fetch_month(origin, dest, month, token):
    qs = urllib.parse.urlencode({
        "origin": origin,
        "destination": dest,
        "departure_at": month,
        "currency": "twd",
        "unique": "true",
        "sorting": "price",
        "one_way": "false",
        "limit": "100",
    })
    req = urllib.request.Request(
        API + "?" + qs,
        headers={"X-Access-Token": token, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            raw = res.read()
            status = res.status
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise TokenRejected(str(e.code))
        return None, e.code
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, 0
    if status != 200:
        return None, status
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        return None, status
    if isinstance(payload, dict) and payload.get("success") is False:
        return None, status
    return offers_from_payload(payload), status


def within_window(date, start, end):
    return start <= date <= end


def merge_offers(chunks, start, end):
    best = {}
    for chunk in chunks:
        for offer in chunk:
            if not within_window(offer["date"], start, end):
                continue
            prev = best.get(offer["date"])
            if prev is None or offer["price_twd"] < prev["price_twd"]:
                best[offer["date"]] = offer
    return [best[k] for k in sorted(best)][:62]


def dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
    if not token:
        log("TRAVELPAYOUTS_TOKEN is not set; leaving tp_prices.json unchanged")
        return 0
    deals = load_json(DEALS, None)
    if not isinstance(deals, dict):
        log("deals.json is missing or unreadable; leaving tp_prices.json unchanged")
        return 0
    routes = collect_routes(deals)
    if not routes:
        log("no routes in deals.json; leaving tp_prices.json unchanged")
        return 0
    old = load_json(OUT, {"routes": {}})
    old_routes = old.get("routes") if isinstance(old, dict) else {}
    if not isinstance(old_routes, dict):
        old_routes = {}
    months = months_ahead(2)
    today = datetime.now(TPE).date().isoformat()
    end = (datetime.now(TPE).date() + timedelta(days=62)).isoformat()
    new_routes = {}
    ok_n = 0
    err_n = 0
    try:
        for origin, dest in routes:
            key = origin + "-" + dest
            chunks = []
            failed = False
            for month in months:
                got, status = fetch_month(origin, dest, month, token)
                if got is None and status == 429:
                    time.sleep(2)
                    got, status = fetch_month(origin, dest, month, token)
                if got is None:
                    failed = True
                    err_n += 1
                    log("Travelpayouts %s %s HTTP %s" % (key, month, status or "error"))
                else:
                    chunks.append(got)
                time.sleep(0.35)
            if chunks and not failed:
                new_routes[key] = merge_offers(chunks, today, end)
                ok_n += 1
            elif key in old_routes and isinstance(old_routes[key], list):
                new_routes[key] = old_routes[key]
                log("kept previous prices for " + key)
            elif chunks:
                new_routes[key] = merge_offers(chunks, today, end)
                ok_n += 1
    except TokenRejected:
        log("Travelpayouts rejected the token; leaving tp_prices.json unchanged")
        return 0
    if ok_n == 0:
        log("no routes updated (%s request errors); leaving tp_prices.json unchanged" % err_n)
        return 0
    doc = {
        "currency": "TWD",
        "routes": new_routes,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    previous = load_json(OUT, None)
    prev_routes = previous.get("routes") if isinstance(previous, dict) else None
    if prev_routes == new_routes:
        log("prices unchanged (%s routes); not rewriting tp_prices.json" % ok_n)
        return 0
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(dump(doc))
    os.replace(tmp, OUT)
    log("wrote %s routes (%s request errors)" % (ok_n, err_n))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log("Travelpayouts fetch failed (%s); leaving tp_prices.json unchanged" % type(e).__name__)
        sys.exit(0)
