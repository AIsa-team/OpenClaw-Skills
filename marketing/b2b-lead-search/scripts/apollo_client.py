#!/usr/bin/env python3
"""
AIsa B2B Lead Search — Python CLI Client
========================================

Search Apollo's B2B database (270M+ contacts / companies) and enrich people
and organizations via the AIsa Apollo relay. Build target-account lists,
find decision-makers, and resolve a person's title, company, and email.

Requires the AISA_API_KEY environment variable.

Usage:
    python3 apollo_client.py companies --keywords "artificial intelligence" --per-page 5
    python3 apollo_client.py companies --keywords "fintech" --employees "50,200" --locations "United States"
    python3 apollo_client.py contacts  --titles "Head of Marketing,VP Marketing" --per-page 5
    python3 apollo_client.py enrich-person --first-name Dylan --last-name Field --company Figma
    python3 apollo_client.py enrich-org --domain stripe.com
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

AISA_BASE = "https://api.aisa.one/apis/v1"


def get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY", "")
    if not key:
        print("Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("Get your key at https://aisa.one", file=sys.stderr)
        sys.exit(1)
    return key


def aisa_post(api_key: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{AISA_BASE}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"API error {e.code} on {path}: {body_text}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error on {path}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def cmd_companies(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body: dict[str, Any] = {"per_page": args.per_page, "page": args.page}
    if args.keywords:
        body["q_organization_keyword_tags"] = _csv(args.keywords)
    if args.locations:
        body["organization_locations"] = _csv(args.locations)
    if args.employees:
        # Format: "min,max" -> Apollo range string "min,max"
        body["organization_num_employees_ranges"] = [args.employees.replace(" ", "")]
    data = aisa_post(api_key, "/apollo/mixed_companies/search", body)

    orgs = data.get("organizations") or data.get("accounts") or []
    pg = data.get("pagination", {})
    print(f"\n{'='*66}")
    print(f"  Company Search — {pg.get('total_entries', '?')} matches "
          f"(page {pg.get('page', '?')}/{pg.get('total_pages', '?')})")
    print(f"{'='*66}\n")
    for i, o in enumerate(orgs, 1):
        print(f"  [{i}] {o.get('name', 'Unknown')}")
        if o.get("primary_domain") or o.get("website_url"):
            print(f"      Domain:    {o.get('primary_domain') or o.get('website_url')}")
        if o.get("industry"):
            print(f"      Industry:  {o.get('industry')}")
        emp = o.get("estimated_num_employees")
        if emp:
            print(f"      Employees: {emp}")
        loc = ", ".join(x for x in [o.get("city"), o.get("state"), o.get("country")] if x)
        if loc:
            print(f"      Location:  {loc}")
        if o.get("linkedin_url"):
            print(f"      LinkedIn:  {o.get('linkedin_url')}")
        print()


def cmd_contacts(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body: dict[str, Any] = {"per_page": args.per_page, "page": args.page}
    if args.titles:
        body["person_titles"] = _csv(args.titles)
    if args.locations:
        body["person_locations"] = _csv(args.locations)
    if args.keywords:
        body["q_organization_keyword_tags"] = _csv(args.keywords)
    data = aisa_post(api_key, "/apollo/contacts/search", body)

    people = data.get("contacts") or data.get("people") or []
    pg = data.get("pagination", {})
    print(f"\n{'='*66}")
    print(f"  Contact Search — {pg.get('total_entries', '?')} matches "
          f"(page {pg.get('page', '?')}/{pg.get('total_pages', '?')})")
    print(f"{'='*66}\n")
    for i, p in enumerate(people, 1):
        print(f"  [{i}] {p.get('name') or '(No name)'}")
        if p.get("title"):
            print(f"      Title:     {p.get('title')}")
        org = p.get("organization") or {}
        if org.get("name") or p.get("organization_name"):
            print(f"      Company:   {org.get('name') or p.get('organization_name')}")
        if p.get("email"):
            print(f"      Email:     {p.get('email')}")
        if p.get("linkedin_url"):
            print(f"      LinkedIn:  {p.get('linkedin_url')}")
        print()


def cmd_enrich_person(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body: dict[str, Any] = {}
    if args.first_name:
        body["first_name"] = args.first_name
    if args.last_name:
        body["last_name"] = args.last_name
    if args.company:
        body["organization_name"] = args.company
    if args.domain:
        body["domain"] = args.domain
    if args.email:
        body["email"] = args.email
    data = aisa_post(api_key, "/apollo/people/match", body)

    p = data.get("person") or {}
    print(f"\n{'='*66}")
    print(f"  Person Enrichment")
    print(f"{'='*66}\n")
    if not p:
        print("  No match found.")
        return
    print(f"  Name:      {p.get('name')}")
    print(f"  Title:     {p.get('title')}")
    print(f"  Email:     {p.get('email') or '(not revealed)'}")
    print(f"  LinkedIn:  {p.get('linkedin_url')}")
    org = p.get("organization") or {}
    if org:
        print(f"  Company:   {org.get('name')} ({org.get('website_url', '')})")
    loc = ", ".join(x for x in [p.get("city"), p.get("state"), p.get("country")] if x)
    if loc:
        print(f"  Location:  {loc}")
    print()


def cmd_enrich_org(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body: dict[str, Any] = {}
    if args.domain:
        body["domain"] = args.domain
    if args.name:
        body["organization_name"] = args.name
    data = aisa_post(api_key, "/apollo/organizations/enrich", body)

    o = data.get("organization") or {}
    print(f"\n{'='*66}")
    print(f"  Organization Enrichment")
    print(f"{'='*66}\n")
    if not o:
        print("  No match found.")
        return
    print(f"  Name:        {o.get('name')}")
    print(f"  Domain:      {o.get('primary_domain') or o.get('website_url')}")
    print(f"  Industry:    {o.get('industry')}")
    print(f"  Employees:   {o.get('estimated_num_employees')}")
    print(f"  Founded:     {o.get('founded_year')}")
    print(f"  LinkedIn:    {o.get('linkedin_url')}")
    if o.get("short_description"):
        print(f"\n  About: {o['short_description'][:400]}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIsa B2B Lead Search (Apollo)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_co = sub.add_parser("companies", help="Search companies / target accounts")
    p_co.add_argument("--keywords", "-k", help="Comma-separated company keywords")
    p_co.add_argument("--locations", "-l", help="Comma-separated HQ locations")
    p_co.add_argument("--employees", help="Employee count range 'min,max' (e.g. '50,200')")
    p_co.add_argument("--per-page", type=int, default=10)
    p_co.add_argument("--page", type=int, default=1)
    p_co.set_defaults(func=cmd_companies)

    p_ct = sub.add_parser("contacts", help="Search saved contacts by title / company")
    p_ct.add_argument("--titles", "-t", help="Comma-separated job titles")
    p_ct.add_argument("--locations", "-l", help="Comma-separated person locations")
    p_ct.add_argument("--keywords", "-k", help="Comma-separated company keywords")
    p_ct.add_argument("--per-page", type=int, default=10)
    p_ct.add_argument("--page", type=int, default=1)
    p_ct.set_defaults(func=cmd_contacts)

    p_ep = sub.add_parser("enrich-person", help="Resolve a person's title/company/email")
    p_ep.add_argument("--first-name")
    p_ep.add_argument("--last-name")
    p_ep.add_argument("--company", help="Organization name")
    p_ep.add_argument("--domain", help="Company domain")
    p_ep.add_argument("--email")
    p_ep.set_defaults(func=cmd_enrich_person)

    p_eo = sub.add_parser("enrich-org", help="Enrich a company by domain or name")
    p_eo.add_argument("--domain")
    p_eo.add_argument("--name")
    p_eo.set_defaults(func=cmd_enrich_org)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
