#!/usr/bin/env python3
"""Portable AISA Router adapter using Python HTTPS and AISA_API_KEY."""
from __future__ import annotations

import argparse
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import urllib.request
import urllib.error
import http.client
import ssl
from urllib.parse import urlsplit
import uuid

HOST = 'https://tools.aisa.one'
PREFIX = '/v1/tool-router/'
ROUTES = {'schema': PREFIX + 'aisa-batch-get-schema',
          'quote': PREFIX + 'aisa-batch-quote', 'use': PREFIX + 'aisa-batch-use'}
COST = 'x-aisa-customer-cost-micros-usd'
DEFAULT_BUDGET = 2_000_000
CAPS = json.loads(Path(__file__).with_name('capabilities.json').read_text())


class Invalid(ValueError):
    pass


class TransportError(Exception):
    pass


def decode(text):
    def reject(value):
        raise Invalid('non_finite_json')
    def finite(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            reject(value)
        return parsed
    return json.loads(text, parse_constant=reject, parse_float=finite)


def integer(value):
    return type(value) is int and value >= 0


def require(condition, message):
    if not condition:
        raise Invalid(message)


def validate(value, schema):
    """Validate the limited schema vocabulary used by these two tools; fail on drift."""
    annotations = {'title', 'description', 'default', 'example', 'examples', 'deprecated',
                   'readOnly', 'writeOnly', '$schema'}
    supported = {'type', 'properties', 'required', 'additionalProperties', 'items',
                 'minItems', 'maxItems', 'minLength', 'maxLength', 'minimum', 'maximum',
                 'enum', 'const', 'anyOf', 'oneOf', 'allOf', 'pattern', 'format'}
    require(isinstance(schema, dict), 'schema_invalid')
    require(not (set(schema) - annotations - supported), 'schema_vocabulary_changed')
    for operator in ('anyOf', 'oneOf', 'allOf'):
        if operator in schema:
            outcomes = []
            for branch in schema[operator]:
                try:
                    validate(value, branch)
                    outcomes.append(True)
                except Invalid:
                    outcomes.append(False)
            require((sum(outcomes) == 1 if operator == 'oneOf' else
                     all(outcomes) if operator == 'allOf' else any(outcomes)), 'schema_union')
    types = {'object': lambda x: isinstance(x, dict), 'array': lambda x: isinstance(x, list),
             'string': lambda x: isinstance(x, str), 'integer': lambda x: type(x) is int,
             'number': lambda x: type(x) in (int, float), 'boolean': lambda x: type(x) is bool,
             'null': lambda x: x is None}
    if 'type' in schema:
        ts = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        require(all(t in types for t in ts) and any(types[t](value) for t in ts), 'schema_type')
    if 'enum' in schema:
        require(any(type(value) is type(v) and value == v for v in schema['enum']), 'schema_enum')
    if 'const' in schema:
        require(type(value) is type(schema['const']) and value == schema['const'], 'schema_const')
    if isinstance(value, dict):
        require(set(schema.get('required', [])) <= set(value), 'schema_required')
        props = schema.get('properties', {})
        for k, v in value.items():
            rule = props.get(k, schema.get('additionalProperties', True))
            require(rule is not False, 'schema_unknown_parameter')
            if isinstance(rule, dict):
                validate(v, rule)
    if isinstance(value, list):
        require(schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', len(value)), 'schema_array_size')
        for item in value:
            if 'items' in schema:
                validate(item, schema['items'])
    if isinstance(value, str):
        require(schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', len(value)), 'schema_string_size')
        if 'pattern' in schema:
            require(re.search(schema['pattern'], value) is not None, 'schema_pattern')
        if schema.get('format') == 'date':
            import datetime
            try:
                datetime.date.fromisoformat(value)
            except ValueError as exc:
                raise Invalid('schema_date') from exc
        elif schema.get('format') not in (None, 'uri', 'url'):
            raise Invalid('schema_format_changed')
    if type(value) in (int, float):
        require(schema.get('minimum', value) <= value <= schema.get('maximum', value), 'schema_number_range')


def arguments(capability, raw):
    require(capability in CAPS, 'unknown_capability')
    cap = CAPS[capability]
    require(isinstance(raw, dict) and set(raw) <= set(cap['allowed']), 'unsupported_arguments')
    result = {**cap['defaults'], **raw}
    if capability == 'search':
        require(isinstance(raw.get('query'), str) and 0 < len(raw['query'].strip()) <= 2000, 'query_required')
        require(type(result['max_results']) is int and 1 <= result['max_results'] <= 5, 'max_results_1_to_5')
    elif capability == 'extract':
        urls = raw.get('urls')
        if isinstance(urls, str):
            urls = [urls]
        require(isinstance(urls, list) and 1 <= len(urls) <= 3, 'urls_1_to_3')
        for url in urls:
            require(isinstance(url, str) and len(url) <= 4096, 'invalid_url')
            u = urlsplit(url)
            require(u.scheme == 'https' and u.hostname and not u.username and not u.password
                    and u.port in (None, 443), 'public_https_url_required')
            host = u.hostname.lower()
            require('.' in host and not host.endswith(('.local', '.internal', '.localhost')),
                    'public_hostname_required')
            try:
                address = ipaddress.ip_address(host)
            except ValueError:
                address = None
            require(address is None or address.is_global, 'private_address')
        result['urls'] = urls
    elif capability == 'similar':
        require(result.get('platform') in ('youtube', 'tiktok'), 'platform_unsupported')
        require(type(result['limit']) is int and 1 <= result['limit'] <= 10, 'limit_1_to_10')
        direction = raw.get('contentDirection')
        seed = raw.get('seedProfileUrl')
        require(bool(direction) or bool(seed), 'seed_or_direction_required')
        if direction is not None:
            require(isinstance(direction, str) and 0 < len(direction.strip()) <= 800, 'direction_invalid')
        if seed is not None:
            creator_url(seed, result['platform'])
        filters = raw.get('filters', {})
        require(isinstance(filters, dict), 'filters_invalid')
        require('region' not in filters, 'filters.region_invalid_use_regions_array')
        require(set(filters) <= {'regions', 'languages', 'minFollowers', 'maxFollowers', 'minVideosAverageViews', 'maxVideosAverageViews'}, 'filters_unknown_allowed_regions_languages_minFollowers_maxFollowers_minVideosAverageViews_maxVideosAverageViews')
        for field in ('regions', 'languages'):
            if field in filters:
                require(isinstance(filters[field], list) and 1 <= len(filters[field]) <= 10
                        and all(isinstance(v, str) and 0 < len(v) <= 20 for v in filters[field]), 'filter_list_invalid')
        for low, high in [('minFollowers', 'maxFollowers'), ('minVideosAverageViews', 'maxVideosAverageViews')]:
            for field in (low, high):
                if field in filters:
                    require(integer(filters[field]), 'filter_number_invalid')
            require(low not in filters or high not in filters or filters[low] <= filters[high], 'filter_range_invalid')
    elif capability == 'email':
        creator_url(raw.get('url'))
    elif capability in ('instagram-profile', 'instagram-posts'):
        require(isinstance(raw.get('handle'), str) and re.fullmatch(r'[A-Za-z0-9_.]{1,30}', raw['handle']), 'handle_invalid')
    elif capability == 'youtube-search':
        require(isinstance(raw.get('q'), str) and 0 < len(raw['q'].strip()) <= 500, 'query_required')
    return result


def creator_url(url, platform=None):
    require(isinstance(url, str) and len(url) <= 2048, 'creator_url_required')
    u = urlsplit(url)
    hosts = {'youtube': {'youtube.com', 'www.youtube.com'},
             'tiktok': {'tiktok.com', 'www.tiktok.com'},
             'instagram': {'instagram.com', 'www.instagram.com'}}
    require(u.scheme == 'https' and not u.username and not u.password and u.port in (None, 443)
            and not u.query and not u.fragment, 'creator_https_profile_required')
    found = next((k for k, hs in hosts.items() if u.hostname in hs), None)
    require(found is not None and (platform is None or found == platform), 'creator_platform_mismatch')
    path = u.path.strip('/')
    if found == 'youtube':
        valid = re.fullmatch(r'@[A-Za-z0-9_.-]+|(?:channel|c|user)/[A-Za-z0-9_.-]+', path)
    elif found == 'tiktok':
        valid = re.fullmatch(r'@[A-Za-z0-9_.]+', path)
    else:
        valid = re.fullmatch(r'[A-Za-z0-9_.]{1,30}', path) and path not in {'p', 'reel', 'explore', 'stories'}
    require(bool(valid), 'creator_profile_path_required')


def usable_result(capability, data):
    if not isinstance(data, dict) or data.get('success') is False or data.get('error'):
        return False
    if capability in ('search', 'extract'):
        return isinstance(data.get('results'), list)
    if capability in ('similar', 'email'):
        if data.get('code') != 1000 or not isinstance(data.get('data'), dict):
            return False
        payload = data['data']
        if capability == 'similar':
            return isinstance(payload.get('data'), list)
        return 'email' in payload and (payload['email'] is None or isinstance(payload['email'], str)) and isinstance(payload.get('emails'), list)
    if capability == 'instagram-profile':
        payload = data.get('data')
        return isinstance(payload, dict) and isinstance(payload.get('user'), dict) and bool(payload['user'].get('username'))
    if capability == 'instagram-posts':
        return isinstance(data.get('items'), list)
    if capability == 'youtube-search':
        return any(isinstance(data.get(key), list) for key in ('videos', 'channels', 'shorts', 'sections'))
    return False


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def skill_user_agent():
    frontmatter = (Path(__file__).resolve().parents[1] / 'SKILL.md').read_text().split('---', 2)[1]
    name = re.search(r'^name: ([a-z0-9-]+)$', frontmatter, re.M)
    version = re.search(r'^  version: "([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)"$', frontmatter, re.M)
    require(name is not None and version is not None, 'invalid_skill_metadata')
    return f'aisa-skill/{version[1]} (skill={name[1]})'


def python_request(kind, payload):
    require(kind in ROUTES, 'unknown_router_method')
    key = os.environ.get('AISA_API_KEY', '').strip()
    require(bool(key), 'AISA_API_KEY_required')
    require(not any(ord(c) < 32 or ord(c) > 126 for c in key), 'invalid_api_key')
    request = urllib.request.Request(
        HOST + ROUTES[kind],
        data=json.dumps(payload, allow_nan=False).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                 'Authorization': 'Bearer ' + key, 'User-Agent': skill_user_agent()}, method='POST')
    opener = urllib.request.build_opener(NoRedirect())
    try:
        try:
            response = opener.open(request, timeout=60)
        except urllib.error.HTTPError as exc:
            response = exc  # Preserve HTTP status and any settlement headers.
        with response:
            status = response.code
            headers = {k.lower(): v.strip() for k, v in response.headers.items()}
            raw = response.read(16 * 1024 * 1024 + 1)
        if 300 <= status < 400:
            raise TransportError(kind + '_redirect_refused')
        if len(raw) > 16 * 1024 * 1024:
            raise TransportError(kind + '_response_too_large')
        try:
            data = decode(raw.decode('utf-8'))
        except (ValueError, UnicodeError):
            if status >= 400:
                return status, headers, {'error': {'message': 'Non-JSON HTTP error response',
                                                  'content_type': headers.get('content-type')}}
            raise TransportError(kind + '_invalid_json_response') from None
        return status, headers, data
    except TransportError:
        raise
    except (TimeoutError, ssl.SSLError, urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        cause = exc.reason if isinstance(exc, urllib.error.URLError) else exc
        if isinstance(cause, TimeoutError):
            reason = 'timeout'
        elif isinstance(cause, ssl.SSLError):
            reason = 'tls_error'
        elif isinstance(cause, http.client.RemoteDisconnected):
            reason = 'connection_closed'
        else:
            reason = 'connection_error'
        raise TransportError(kind + '_' + reason) from None


def batch_result(data, call):
    require(isinstance(data, dict) and isinstance(data.get('results'), list)
            and len(data['results']) == 1, 'invalid_batch_response')
    result = data['results'][0]
    require(isinstance(result, dict) and result.get('call_id') == call['call_id']
            and result.get('tool') == call['tool'] and type(result.get('successful')) is bool,
            'batch_identity_mismatch')
    return result


def quote_budget_amount(result):
    """Approval basis, not a guaranteed ceiling for estimate quotes."""
    require(result.get('successful') is True, 'quote_failed')
    q = result.get('data')
    require(isinstance(q, dict) and q.get('object') == 'cost_estimate' and q.get('currency') == 'USD', 'invalid_quote')
    estimated, ceiling = q.get('estimated_cost_micros_usd'), q.get('max_cost_micros_usd')
    require(integer(estimated) and isinstance(q.get('estimated_at'), str) and q['estimated_at'], 'invalid_quote_amount')
    if q.get('estimate_kind') == 'estimate':
        require(q.get('may_exceed_estimate') is True and 'max_cost_micros_usd' not in q,
                'invalid_estimate_fields')
        return estimated
    require(integer(ceiling) and q.get('may_exceed_estimate') is False, 'invalid_quote_ceiling')
    require((q.get('estimate_kind') == 'exact' and ceiling == estimated) or
            (q.get('estimate_kind') == 'upper_bound' and ceiling >= estimated), 'invalid_quote_kind')
    return ceiling


def run(capability, raw, summary, remaining, execute=False, transport=python_request, session_id=None):
    require(integer(remaining), 'remaining_budget_required')
    require(isinstance(summary, str) and 0 < len(summary.strip()) <= 500, 'task_summary_required')
    args = arguments(capability, raw)
    session = session_id or str(uuid.uuid4())
    tool = CAPS[capability]['tool']
    status, _, data = transport('schema', {'session_id': session, 'tools': [tool],
        'include_arguments_schema': True, 'include_response_schema': True})
    require(status == 200 and isinstance(data, dict) and data.get('session_id') == session, 'schema_request_failed')
    schema = data.get('tools', {}).get(tool, {})
    require(schema.get('successful') is True and isinstance(schema.get('response_schema'), dict), 'schema_unavailable')
    validate(args, schema.get('arguments_schema'))
    call = {'call_id': str(uuid.uuid4()), 'tool': tool, 'arguments': args}
    payload = {'session_id': session, 'calls': [call]}
    status, _, data = transport('quote', payload)
    require(status == 200 and isinstance(data, dict) and data.get('session_id') == session, 'quote_request_failed')
    quoted = batch_result(data, call)
    amount = quote_budget_amount(quoted)
    result = {'session_id': session, 'request_id': call['call_id'], 'quote': quoted['data'],
              'remaining_budget_usd_micros': remaining, 'budget_basis_usd_micros': amount}
    if amount > remaining:
        return {**result, 'status': 'stop', 'reason': 'budget_approval_required',
                'approval': {'summary': summary, 'quoted_cost_usd_micros': amount,
                             'remaining_budget_usd_micros': remaining}}
    if not execute:
        return {**result, 'status': 'ready'}
    # Each attempt consumes its quote; optional fee metadata never hides data.
    result.update(budget_used_usd_micros=amount,
                  remaining_budget_usd_micros=remaining - amount)
    try:
        status, headers, body = transport('use', payload)
    except TransportError as exc:
        return {**result, 'status': 'error', 'reason': str(exc),
                'customer_cost_micros_usd': None}
    h = headers.get(COST)
    actual = int(h) if isinstance(h, str) and re.fullmatch(r'[0-9]+', h) else None
    result.update(http_status=status, customer_cost_micros_usd=actual)
    if status != 200:
        return {**result, 'status': 'error', 'reason': 'use_http_error', 'response': body}
    try:
        require(isinstance(body, dict) and body.get('session_id') == session, 'use_session_mismatch')
        item = batch_result(body, call)
    except Invalid as exc:
        return {**result, 'status': 'error', 'reason': str(exc), 'response': body}
    if actual is None and integer(item.get('customer_cost_micros_usd')):
        result['customer_cost_micros_usd'] = item['customer_cost_micros_usd']
    usable = item['successful'] and usable_result(capability, item.get('data'))
    return {**result, 'status': 'success' if usable else 'error', 'result': item,
            **({} if usable else {'reason': 'tool_failed' if not item['successful'] else 'tool_data_invalid'})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['quote', 'use'])
    parser.add_argument('capability', choices=sorted(CAPS))
    parser.add_argument('--arguments-file', required=True)
    parser.add_argument('--summary', required=True)
    parser.add_argument('--remaining-budget-usd-micros', type=int, required=True,
                        help='Remaining task allowance, tracked by the calling Agent; initial default is 2000000')
    parser.add_argument('--session-id')
    cli = parser.parse_args()
    try:
        result = run(cli.capability, decode(Path(cli.arguments_file).read_text()), cli.summary,
                     cli.remaining_budget_usd_micros, cli.command == 'use', session_id=cli.session_id)
    except (Invalid, TransportError, ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
        result = {'status': 'stop', 'reason': str(exc) if isinstance(exc, (Invalid, TransportError)) else 'input_or_state_error'}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result['status'] in ('ready', 'success') else 3


if __name__ == '__main__':
    raise SystemExit(main())
