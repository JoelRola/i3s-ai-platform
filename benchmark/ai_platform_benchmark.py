#!/usr/bin/env python3
"""Bounded, local-only I3S Ollama benchmark and dual-GPU proof runner.

Results are append-free run directories: CSV request records, JSON summary, and
for --dual-proof a one-second GPU sample CSV plus a human-readable verdict.
"""
import argparse, csv, datetime as dt, json, os, statistics, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path('/home/jorola/i3s_ai_ops/benchmark/results')
FIELDS = ['timestamp','model','quantisation_tag','gpu','prompt_tokens','output_tokens','context_request_size','concurrency','cold_or_warm','TTFT_seconds','total_latency_seconds','generation_tokens_per_second','prompt_eval_tokens_per_second','VRAM_peak_MiB','GPU_util_peak_percent','RAM_peak_MiB','success','http_status_error','error_type']
PROMPTS = {
 'short': 'Explain, in one concise paragraph, why a local AI platform needs a health check. ' * 45,
 'medium': 'Summarize this operations note accurately: requests go from a private UI through a gateway to a GPU model server; observe errors, latency, memory, and service health. ' * 180,
 'long': 'Summarize the following platform operations note accurately and concisely. A private local AI platform routes requests through an interface and gateway to a CUDA model service. Correct GPU isolation, predictable latency, resource monitoring, and recoverable deployment are essential. ' * 620,
}
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def post(url, payload, timeout=600):
    req=Request(url, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    with build_opener(ProxyHandler({})).open(req, timeout=timeout) as r: return json.load(r)
def gpu_sample():
    q='index,uuid,name,utilization.gpu,memory.used,power.draw,temperature.gpu'
    p=subprocess.run(['nvidia-smi','--query-gpu='+q,'--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
    rows=[]
    for x in p.stdout.strip().splitlines():
        a=[v.strip() for v in x.split(',')]
        if len(a)==7: rows.append(dict(timestamp=utc(),gpu_index=a[0],uuid=a[1],gpu_name=a[2],utilization_percent=a[3],memory_used_MiB=a[4],power_watts=a[5],temperature_C=a[6]))
    apps=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,gpu_uuid,used_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=10)
    return rows, '; '.join(x.strip() for x in apps.stdout.splitlines() if x.strip()) or 'none'
def ram_mib():
    d=dict(x.split(':',1) for x in open('/proc/meminfo') if ':' in x); return round((int(d['MemTotal'].split()[0])-int(d['MemAvailable'].split()[0]))/1024,1)
def generate(prompt, output, state):
    started=time.monotonic(); before,_=gpu_sample(); peak=max(float(x['memory_used_MiB']) for x in before); util=max(float(x['utilization_percent']) for x in before); err=''; data={}
    try:
        data=post('http://127.0.0.1:11434/api/generate',{'model':'qwen3.5:9b','prompt':prompt,'stream':False,'options':{'temperature':0,'num_predict':output}},900)
        if data.get('error'): raise RuntimeError(data['error'])
    except Exception as e: err=str(e)
    after,_=gpu_sample()
    for x in after: peak=max(peak,float(x['memory_used_MiB'])); util=max(util,float(x['utilization_percent']))
    total=time.monotonic()-started; load=data.get('load_duration',0)/1e9; pe=data.get('prompt_eval_duration',0)/1e9; ev=data.get('eval_duration',0)/1e9
    evaln=data.get('eval_count',0); pen=data.get('prompt_eval_count',0)
    return dict(timestamp=utc(),model='i3s-main/qwen3.5:9b',quantisation_tag='qwen3.5:9b',gpu='A100',prompt_tokens=pen or '',output_tokens=evaln or '',context_request_size=state['size'],concurrency=state['concurrency'],cold_or_warm=state['warm'],TTFT_seconds=round(load+pe,4) if data else '',total_latency_seconds=round(total,4),generation_tokens_per_second=round(evaln/ev,3) if ev else '',prompt_eval_tokens_per_second=round(pen/pe,3) if pe else '',VRAM_peak_MiB=peak,GPU_util_peak_percent=util,RAM_peak_MiB=ram_mib(),success=not err,http_status_error='',error_type=err)
def aggregate(rows):
    ok=[r for r in rows if r['success']]; vals=lambda k: sorted(float(r[k]) for r in ok if r[k]!='')
    pct=lambda xs,p: '' if not xs else round(xs[min(len(xs)-1, max(0, int((len(xs)-1)*p)))],4)
    return {'request_count':len(rows),'success_count':len(ok),'error_count':len(rows)-len(ok),'error_rate':round((len(rows)-len(ok))/len(rows),4) if rows else 0,'p50_TTFT':pct(vals('TTFT_seconds'),.5),'p95_TTFT':pct(vals('TTFT_seconds'),.95),'p50_total_latency':pct(vals('total_latency_seconds'),.5),'p95_total_latency':pct(vals('total_latency_seconds'),.95),'mean_tokens_per_second':round(statistics.mean(vals('generation_tokens_per_second')),4) if vals('generation_tokens_per_second') else '','p50_tokens_per_second':pct(vals('generation_tokens_per_second'),.5),'p95_tokens_per_second':pct(vals('generation_tokens_per_second'),.95)}
def dual(out):
    samples=[]; stop=threading.Event()
    def sampler():
        while not stop.is_set():
            g,apps=gpu_sample()
            for x in g: x['processes']=apps; samples.append(x)
            stop.wait(1)
    t=threading.Thread(target=sampler,daemon=True); t.start(); started=time.monotonic()
    # Long generation and a large independent embedding batch overlap deliberately.
    with ThreadPoolExecutor(max_workers=2) as ex:
        a=ex.submit(generate, PROMPTS['medium'], 1024, {'size':'dual','concurrency':1,'warm':'warm'})
        b=ex.submit(post,'http://127.0.0.1:11435/api/embed',{'model':'qwen3-embedding:4b','input':[PROMPTS['medium']]*24},900)
        gen=a.result(); emb=b.result()
    elapsed=time.monotonic()-started; stop.set(); t.join(2)
    with (out/'dual_gpu_proof.csv').open('w',newline='') as f: csv.DictWriter(f,fieldnames=['timestamp','gpu_index','uuid','gpu_name','utilization_percent','memory_used_MiB','power_watts','temperature_C','processes']).writeheader(); csv.DictWriter(f,fieldnames=['timestamp','gpu_index','uuid','gpu_name','utilization_percent','memory_used_MiB','power_watts','temperature_C','processes']).writerows(samples)
    a100=max((float(x['utilization_percent']) for x in samples if 'A100' in x['gpu_name']),default=0); p100=max((float(x['utilization_percent']) for x in samples if 'P100' in x['gpu_name']),default=0)
    verdict='PASS' if gen['success'] and emb.get('embeddings') and a100>0 and p100>0 else 'FAIL'
    (out/'dual_gpu_proof.txt').write_text(f'{verdict}: simultaneous generation and embedding completed. generation_latency_s={gen["total_latency_seconds"]}; generation_tok_s={gen["generation_tokens_per_second"]}; embedding_latency_s={elapsed:.3f}; A100_peak_util={a100}; P100_peak_util={p100}; embedding_count={len(emb.get("embeddings",[]))}.\n')
    print((out/'dual_gpu_proof.txt').read_text().strip()); return verdict
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--dual-proof',action='store_true'); ap.add_argument('--sizes',nargs='+',choices=PROMPTS,default=['short','medium','long']); ap.add_argument('--outputs',nargs='+',type=int,default=[128]); ap.add_argument('--concurrency',nargs='+',type=int,default=[1,2,4,8]); ap.add_argument('--repetitions',type=int,default=5); ap.add_argument('--cold',action='store_true'); args=ap.parse_args()
 out=ROOT/dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); out.mkdir(parents=True,exist_ok=True)
 if args.dual_proof: dual(out); return
 rows=[]
 for size in args.sizes:
  for output in args.outputs:
   for c in args.concurrency:
    state={'size':size,'concurrency':c,'warm':'cold' if args.cold else 'warm'}; jobs=[(PROMPTS[size],output,state)]*(args.repetitions*c)
    with ThreadPoolExecutor(max_workers=c) as ex: rows += [x.result() for x in as_completed([ex.submit(generate,*j) for j in jobs])]
 with (out/'results.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
 s=aggregate(rows); (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n'); (out/'summary.md').write_text('# I3S benchmark summary\n\n'+ '\n'.join(f'- {k}: {v}' for k,v in s.items())+'\n'); print(json.dumps(s,indent=2))
if __name__=='__main__': main()
