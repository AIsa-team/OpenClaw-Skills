import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[3]


def modules():
    for category, name in (('marketing', 'creator-marketing'),):
        path = ROOT / category / name / 'scripts/request.py'
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        yield mod


class Response(io.BytesIO):
    code = 200
    headers = {'X-Aisa-Customer-Cost-Micros-Usd': '60'}


class PortableRouterTests(unittest.TestCase):
    def test_auth_post_json_headers_and_no_redirect_handler(self):
        for m in modules():
            with patch.dict(os.environ, {'AISA_API_KEY': 'test-only-key'}), patch.object(m.urllib.request, 'build_opener') as build:
                build.return_value.open.return_value = Response(b'{"ok":true}')
                code, headers, data = m.python_request('quote', {'example': '中文'})
                request = build.return_value.open.call_args.args[0]
                self.assertEqual(request.get_header('Authorization'), 'Bearer test-only-key')
                if Path(m.__file__).parents[1].name == 'creator-marketing':
                    self.assertEqual(request.get_header('User-agent'), 'aisa-skill/0.0.1 (skill=creator-marketing)')
                self.assertEqual(request.full_url, 'https://tools.aisa.one/v1/tool-router/aisa-batch-quote')
                self.assertEqual(request.get_method(), 'POST')
                self.assertEqual(json.loads(request.data), {'example': '中文'})
                self.assertEqual((code, headers[m.COST], data), (200, '60', {'ok': True}))
                self.assertIsNone(build.call_args.args[0].redirect_request(None,None,302,'',{},'https://other.test'))
                build.return_value.open.assert_called_once()

    def test_missing_key_fails_before_network(self):
        for m in modules():
            with patch.dict(os.environ, {}, clear=True), patch.object(m.urllib.request,'build_opener') as build:
                with self.assertRaisesRegex(m.Invalid,'AISA_API_KEY_required'): m.python_request('quote',{})
                build.assert_not_called()

    def test_http_error_status_and_charge_preserved(self):
        for m in modules():
            with patch.dict(os.environ, {'AISA_API_KEY':'test-only-key'}), patch.object(m.urllib.request,'build_opener') as build:
                build.return_value.open.side_effect=urllib.error.HTTPError('https://tools.aisa.one',429,'rate',{'X-Aisa-Customer-Cost-Micros-Usd':'60'},io.BytesIO(b'{"error":"rate"}'))
                code,headers,_=m.python_request('use',{})
                self.assertEqual(code,429);self.assertEqual(headers[m.COST],'60')
                build.return_value.open.assert_called_once()

    def test_redirect_invalid_json_oversize_and_timeout(self):
        for m in modules():
            for mode in ('redirect','json','oversize','timeout'):
                with patch.dict(os.environ, {'AISA_API_KEY':'test-only-key'}), patch.object(m.urllib.request,'build_opener') as build:
                    r=Response(b'bad' if mode=='json' else (b' '*(16*1024*1024+1) if mode=='oversize' else b'{}'))
                    if mode=='redirect': r.code=302
                    if mode=='timeout':build.return_value.open.side_effect=TimeoutError('contains-secret-test-only-key')
                    else:build.return_value.open.return_value=r
                    with self.assertRaises(m.TransportError) as caught:m.python_request('use',{})
                    self.assertNotIn('test-only-key',str(caught.exception))
                    self.assertTrue(str(caught.exception).startswith('use_'))
                    build.return_value.open.assert_called_once()

    def test_budget_stop_settlement_and_unknown_cost(self):
        for m in modules():
            for mode in ('over','success','unknown','mismatch','header-only','item-only','provider-error','timeout','http-error','identity-error'):
                calls=[]
                def transport(kind,payload):
                    calls.append((kind,payload))
                    if kind=='schema':
                        return 200,{}, {'session_id':payload['session_id'],'tools':{payload['tools'][0]:{'successful':True,'read_only':True,'arguments_schema':{'type':'object'},'response_schema':{}}}}
                    call=payload['calls'][0]
                    item={'call_id':call['call_id'],'tool':call['tool'],'successful':True}
                    if kind=='quote':
                        item['data']={'object':'cost_estimate','currency':'USD','estimate_kind':'estimate','estimated_cost_micros_usd':100,'may_exceed_estimate':True,'estimated_at':'now'}
                    else:
                        if mode=='timeout':raise m.TransportError('use_transport_or_response_error')
                        item.update(data={'results':[]},customer_cost_micros_usd=70 if mode=='mismatch' else 60)
                        if mode in ('unknown','header-only'):item.pop('customer_cost_micros_usd')
                        if mode=='provider-error':item.update(successful=False,error={'message':'upstream unavailable'})
                        if mode=='identity-error':item['call_id']='wrong-call'
                    return (502 if kind=='use' and mode=='http-error' else 200),({m.COST:'60'} if mode not in ('unknown','item-only') else {}),{'session_id':payload['session_id'],'results':[item]}
                kwargs={'session_id':'session','transport':transport}
                if hasattr(m,'search'):kwargs['search_id']='search-id'
                out=m.run('search',{'query':'creator research'},'Research creators',50 if mode=='over' else 200,True,**kwargs)
                if mode=='over':
                    self.assertEqual(out['reason'],'budget_approval_required')
                    self.assertEqual([k for k,_ in calls],['schema','quote'])
                    self.assertNotIn('spend_review',out)
                elif mode in ('success','mismatch','header-only','item-only','unknown'):
                    self.assertEqual(out['status'],'success')
                    self.assertEqual(out['customer_cost_micros_usd'],None if mode=='unknown' else 60)
                    self.assertEqual(out['remaining_budget_usd_micros'],100)
                    self.assertEqual(calls[-2][1],calls[-1][1])
                else:
                    self.assertEqual(out['status'],'error')
                    expected={'provider-error':'tool_failed','timeout':'use_transport_or_response_error','http-error':'use_http_error','identity-error':'batch_identity_mismatch'}
                    self.assertEqual(out['reason'],expected[mode])
                    self.assertEqual(out['remaining_budget_usd_micros'],100)
                    if mode=='provider-error':self.assertIn('error',out['result'])
                    if mode in ('http-error','identity-error'):self.assertIn('response',out)
                self.assertNotIn('provider_stop',out)
                self.assertNotIn('ledger_debit_usd_micros',out)
                self.assertNotIn('retry_allowed',out)

    def test_region_correction_preserves_requested_scope(self):
        m=next(modules())
        raw={'platform':'youtube','contentDirection':'camping coffee creators','limit':5,
             'filters':{'region':'US','languages':['en']}}
        with self.assertRaisesRegex(m.Invalid,'use_regions_array'):
            m.arguments('similar',raw)
        raw['filters']={'regions':['US'],'languages':['en']}
        self.assertEqual(m.arguments('similar',raw)['filters'],raw['filters'])

    def test_non_json_http_error_preserves_status_and_fee(self):
        for m in modules():
            with patch.dict(os.environ, {'AISA_API_KEY':'test-only-key'}), patch.object(m.urllib.request,'build_opener') as build:
                r=Response(b'<html>Bad gateway</html>');r.code=502
                build.return_value.open.return_value=r
                status,headers,body=m.python_request('use',{})
                self.assertEqual(status,502)
                self.assertEqual(headers[m.COST],'60')
                self.assertEqual(body['error']['message'],'Non-JSON HTTP error response')

    def test_connection_error_types_remain_distinct(self):
        for m in modules():
            cases=[(TimeoutError(),'timeout'),(m.ssl.SSLError(),'tls_error'),
                   (m.http.client.RemoteDisconnected(),'connection_closed')]
            for error,code in cases:
                with patch.dict(os.environ, {'AISA_API_KEY':'test-only-key'}), patch.object(m.urllib.request,'build_opener') as build:
                    build.return_value.open.side_effect=urllib.error.URLError(error)
                    with self.assertRaisesRegex(m.TransportError,'^schema_'+code+'$'):
                        m.python_request('schema',{})

if __name__=='__main__':unittest.main()
