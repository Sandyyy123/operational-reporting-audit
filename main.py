import argparse,json
from reporting import audit
p=argparse.ArgumentParser(description='Audit synthetic business reporting input')
p.add_argument('--input',default='data/operations.csv');p.add_argument('--start',default='2026-09-01');p.add_argument('--end',default='2026-09-30');p.add_argument('--output',default='audit.json')
a=p.parse_args();report=audit(a.input,a.start,a.end)
with open(a.output,'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
