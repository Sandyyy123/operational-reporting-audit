import csv
import pytest
from reporting import audit

def write(tmp_path,rows):
 p=tmp_path/'data.csv'
 with p.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['record_id','department','booked_date','amount','currency','status']);w.writerows(rows)
 return p

def row(i='a',day='2026-09-01',amount='1.00',currency='USD',status='booked',dept='Sales'):
 return [i,dept,day,amount,currency,status]

def test_fixture():
 r=audit('data/operations.csv');assert r['booked_value']=='3000.00';assert (r['accepted_rows'],r['quarantined_rows'],r['excluded_rows'])==(4,3,2);assert r['release_status']=='review_required';assert r['control_balanced']

def test_duplicate_quarantines_all_members(tmp_path):
 r=audit(write(tmp_path,[row(),row(amount='9.00')]));assert r['quarantined_rows']==2;assert r['booked_value']=='0'

def test_boundaries_and_cancelled(tmp_path):
 r=audit(write(tmp_path,[row('a',day='2026-09-01'),row('b',day='2026-09-30'),row('c',day='2026-10-01'),row('d',status='cancelled')]));assert r['accepted_rows']==2;assert r['excluded_rows']==2

@pytest.mark.parametrize('amount',['NaN','Infinity','-1','1.001','hello'])
def test_bad_amounts(tmp_path,amount):
 r=audit(write(tmp_path,[row(amount=amount)]));assert r['issues'][0]['reasons']==['invalid_amount'];assert r['accepted_rows']==0

def test_no_currency_mixing(tmp_path):
 r=audit(write(tmp_path,[row(currency='EUR')]));assert r['accepted_rows']==0;assert 'unsupported_currency' in r['issues'][0]['reasons']

def test_decimal_exactness(tmp_path):
 r=audit(write(tmp_path,[row('a',amount='0.10'),row('b',amount='0.20')]));assert r['booked_value']=='0.30'

def test_missing_schema(tmp_path):
 p=tmp_path/'bad.csv';p.write_text('a,b\n1,2\n')
 with pytest.raises(ValueError):audit(p)

def test_invalid_date_and_department(tmp_path):
 r=audit(write(tmp_path,[row(day='2026-09-31',dept='Unknown')]));assert set(r['issues'][0]['reasons'])=={'invalid_date','unknown_department'}

def test_source_changes_are_detectable(tmp_path):
 p=write(tmp_path,[row()]);h=audit(p)['input_sha256'];p.write_text(p.read_text().replace('1.00','2.00'));assert h!=audit(p)['input_sha256']
