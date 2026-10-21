"""Read-only zero-quota sports catalog probe. Never log URL, key or response body."""
from datetime import datetime, timezone
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot import NoRedirect

def main():
    row={'endpoint':'https://api.the-odds-api.com/v4/sports/', 'method':'GET',
         'requested_at':datetime.now(timezone.utc).isoformat(),
         'key_present':bool(os.environ.get('THE_ODDS_API_KEY'))}
    if not row['key_present']:
        row['status']='missing_key'
    else:
        url=row['endpoint']+'?'+urlencode({'apiKey':os.environ['THE_ODDS_API_KEY']})
        try:
            with build_opener(NoRedirect()).open(Request(url,method='GET'),timeout=25) as response:
                row['http_status']=response.status
                row['quota']={k:response.headers.get(k) for k in ('x-requests-used','x-requests-remaining','x-requests-last')}
        except HTTPError as exc:
            row['http_status']=exc.code
            row['quota']={k:exc.headers.get(k) for k in ('x-requests-used','x-requests-remaining','x-requests-last')}
            try:
                code=json.loads(exc.read()).get('error_code')
                if code in {'INVALID_KEY','MISSING_KEY','OUT_OF_USAGE_CREDITS'}:
                    row['provider_error_code']=code
            except Exception:
                pass
        except Exception as exc:
            row['error_type']=type(exc).__name__
    row['received_at']=datetime.now(timezone.utc).isoformat()
    print(json.dumps(row,indent=2))

if __name__=='__main__':main()
