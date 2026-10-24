"""Synthetic operational reporting audit. Currency is USD; no FX assumptions."""
import csv, hashlib, json
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

def audit(path, start='2026-09-01', end='2026-09-30'):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if start > end: raise ValueError('start exceeds end')
    rows = list(csv.DictReader(Path(path).open(newline='')))
    required = {'record_id','department','booked_date','amount','currency','status'}
    if not rows or not required <= rows[0].keys(): raise ValueError('missing data or columns')
    counts = Counter(r['record_id'] for r in rows)
    issues, accepted, excluded = [], [], []
    for lineno,r in enumerate(rows,2):
        errors=[]
        if not r['record_id'].strip(): errors.append('missing_id')
        elif counts[r['record_id']] > 1: errors.append('duplicate_id')
        if r['department'] not in {'Sales','Services'}: errors.append('unknown_department')
        if r['currency'] != 'USD': errors.append('unsupported_currency')
        if r['status'] not in {'booked','cancelled'}: errors.append('unknown_status')
        try:
            value=Decimal(r['amount'])
            if not value.is_finite() or value<0 or value.as_tuple().exponent < -2: raise InvalidOperation
        except InvalidOperation: errors.append('invalid_amount'); value=None
        try: day=date.fromisoformat(r['booked_date'])
        except ValueError: errors.append('invalid_date'); day=None
        if errors:
            issues.append({'line':lineno,'id':r['record_id'],'reasons':errors});continue
        if r['status']=='cancelled' or not start<=day<=end:
            excluded.append({'line':lineno,'reason':'cancelled' if r['status']=='cancelled' else 'outside_period'});continue
        accepted.append((r,value))
    totals={d:sum((v for r,v in accepted if r['department']==d),Decimal('0')) for d in ('Sales','Services')}
    return {'period':[str(start),str(end)],'currency':'USD','input_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'input_rows':len(rows),'accepted_rows':len(accepted),'quarantined_rows':len(issues),'excluded_rows':len(excluded),
            'control_balanced':len(rows)==len(accepted)+len(issues)+len(excluded),
            'booked_value':str(sum(totals.values(),Decimal('0'))),'department_totals':{k:str(v) for k,v in totals.items()},
            'issues':issues,'exclusions':excluded,
            'metric_definition':'Booked USD value: sum of noncancelled, valid, unique records dated inside the inclusive period. Not cash receipts, accounting revenue or profit.',
            'release_status':'review_required' if issues else 'passed'}
