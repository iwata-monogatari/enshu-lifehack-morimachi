"""確認済みの公式情報源の一時停止を対象ページだけに注記する。"""
from pathlib import Path
import json,re,html
ROOT=Path(__file__).resolve().parent.parent
START='<!-- VERIFIED-SOURCE-NOTICE:START -->'
END='<!-- VERIFIED-SOURCE-NOTICE:END -->'
def main():
 for row in json.loads((ROOT/'data/verified-source-notices.json').read_text(encoding='utf8')):
  page=ROOT/(row['path'].strip('/')+'/index.html');raw=page.read_bytes().decode('utf8')
  block=START+'<aside class="note" aria-label="公式情報源の確認"><p>'+html.escape(row['message'])+'</p><p><a href="'+html.escape(row['source'],quote=True)+'">'+html.escape(row['label'])+'</a></p></aside>'+END
  if START in raw:out=re.sub(re.escape(START)+'.*?'+re.escape(END),lambda m:block,raw,flags=re.S)
  else:out,n=re.subn(r'</h1>',lambda m:m[0]+block,raw,count=1);assert n==1,page
  if out!=raw:page.write_bytes(out.encode('utf8'))
if __name__=='__main__':main()
