"""Compare manually exported DAX outputs with SQL targets; never fabricate DAX results."""
import csv
from pathlib import Path
import argparse

def compare_files(expected,actual,output,tolerance=1e-8):
    def load(path,value):
        with Path(path).open(newline='',encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        indexed={}
        for row in rows:
            key=(row['measure'],row['filter_context'])
            if key in indexed: raise ValueError('Duplicate measure/filter context')
            indexed[key]=row.get(value,'')
        return indexed
    targets=load(expected,'expected_sql_value'); observations=load(actual,'actual_dax_value'); results=[]
    if set(observations)-set(targets): raise ValueError('Actual export contains unknown measure/context')
    for key,wanted in targets.items():
        got=observations.get(key,'')
        if got.strip()=='': status='PENDING'
        elif wanted.strip()=='': status='PASS' if got.strip().upper()=='BLANK' else 'FAIL'
        else:
            try: status='PASS' if abs(float(got)-float(wanted))<=tolerance else 'FAIL'
            except ValueError: status='FAIL'
        results.append(dict(measure=key[0],filter_context=key[1],expected_sql_value=wanted,actual_dax_value=got,status=status))
    with Path(output).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    return all(r['status']=='PASS' for r in results),results

def main():
    p=argparse.ArgumentParser(description='Compare real DAX observations against SQL targets')
    p.add_argument('--expected',default='powerbi/MEASURE_EXPECTATIONS.csv');p.add_argument('--actual',required=True);p.add_argument('--out',default='reports/POWER_BI_RECONCILIATION.csv')
    a=p.parse_args();passed,_=compare_files(a.expected,a.actual,a.out)
    raise SystemExit(0 if passed else 1)
if __name__=='__main__': main()
