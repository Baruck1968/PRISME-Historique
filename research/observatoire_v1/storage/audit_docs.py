"""Fetch public documentation only; no credentials, uploads, accounts or odds calls."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from urllib.request import urlopen
SOURCES={
 'github_private':'https://docs.github.com/en/get-started/learning-about-github/githubs-plans',
 'github_backup':'https://docs.github.com/en/repositories/archiving-a-github-repository/backing-up-a-repository',
 'github_files':'https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github',
 'github_artifacts':'https://docs.github.com/en/actions/administering-github-actions/usage-limits-and-billing',
 'google_quota':'https://support.google.com/drive/answer/6374270?hl=en',
 'google_inactive':'https://support.google.com/accounts/answer/12418290?hl=en',
 'google_versions':'https://support.google.com/drive/answer/2409045?hl=en',
 'google_trash':'https://support.google.com/drive/answer/2375102?hl=en',
 'rclone_drive':'https://rclone.org/drive/',
 'rclone_crypt':'https://rclone.org/crypt/',
}
def main():
 root=Path(__file__).resolve().parent;stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');cache=root/'.cache'/stamp;cache.mkdir(parents=True)
 def fetch(item):
  name,url=item;row={'name':name,'url':url,'attempted_at':datetime.now(timezone.utc).isoformat()}
  try:
   with urlopen(url,timeout=20) as r:
    raw=r.read();row.update(status=r.status,final_url=r.url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));(cache/(name+'.html')).write_bytes(raw)
  except Exception as exc:row.update(error_type=type(exc).__name__,error=str(exc))
  return row
 with ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(fetch,SOURCES.items()))
 (root/('sources_'+stamp+'.json')).write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps([{'name':r['name'],'status':r.get('status'),'error':r.get('error')} for r in rows],indent=2))
if __name__=='__main__':main()
