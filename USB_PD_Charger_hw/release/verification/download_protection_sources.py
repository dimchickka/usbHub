from pathlib import Path
import urllib.request
root=Path(__file__).resolve().parents[3];dest=root/'documents/Protection';dest.mkdir(exist_ok=True)
urls={
 'Bel_0680H.pdf':'https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-CP-0680H-series.pdf',
 'Bel_0679L.pdf':'https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-cp-0679l-series.pdf',
 'MeanWell_RSP1500.pdf':'https://www.meanwell.com/Upload/PDF/RSP-1500/RSP-1500-SPEC.PDF',
 'Phoenix_1933613.pdf':'https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mkds-5-2-635-bk-z1l-1933613?type=pdf'}
for name,url in urls.items():
 p=dest/name
 if p.exists():assert p.read_bytes().startswith(b'%PDF');continue
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=45) as response:data=response.read()
 assert data.startswith(b'%PDF'),(name,data[:50]);p.write_bytes(data);print('DOWNLOADED',name,len(data),flush=True)
