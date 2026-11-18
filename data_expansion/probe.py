"""One bounded anonymous direct request per official endpoint; metadata only.

No proxy fallback, keys, subscriptions, retries or import of the fetched body.
CI is an independent access observation, never a relay for a denied runtime.
"""
import argparse,json
from news_pilot.ingest import fetch,utc,safe_header
from event_history.__main__ import new_output

ENDPOINTS={
 'world_bank_monthly_xls':'https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx',
 'sec_wework_withdrawal':'https://www.sec.gov/Archives/edgar/data/1533523/000119312519258913/d808793drw.htm',
 'fed_eurusd':'https://www.federalreserve.gov/releases/h10/hist/dat00_eu.htm',
}


def probe(client=fetch,clock=utc,environment='runtime'):
    rows=[]
    for name,url in ENDPOINTS.items():
        try:status,payload,headers=client(url,{})
        except Exception:status,payload,headers=0,b'',{}
        rows.append(dict(source=name,url=url,observed_at=clock(),http_status=status,
           body_bytes_observed=len(payload),transport_denial=safe_header(headers,'X-Pilot-Transport-Denial')=='true',
           result='http_access_only_not_data_or_licence_verification' if status==200 else 'unavailable_no_import',
           content_type=safe_header(headers,'Content-Type'),imported_rows=0,original_http_sha256=None))
    return dict(schema_version=1,environment=environment,receipts=rows,cost_GBP='0.00',
       note='Direct bounded no-retry requests, fixed anonymous official URLs. No body/headers/credential saved, no redistribution inference. Reader transcription access is separate from this runtime/CI HTTP test.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--environment',choices=['runtime','github_actions'],default='runtime')
    a=p.parse_args();r=probe(environment=a.environment);new_output(a.output,r);print(json.dumps(r,indent=2))

if __name__=='__main__':main()
