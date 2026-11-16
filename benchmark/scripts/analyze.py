#!/usr/bin/env python3
"""Summarize one complete run directory created by run.py."""
import argparse
import json
from pathlib import Path
import statistics

p = argparse.ArgumentParser()
p.add_argument('run', type=Path)
a = p.parse_args()
def rows(name):
    return [json.loads(line) for line in (a.run / name).read_text().splitlines()]
ready = json.loads((a.run / 'readiness.json').read_text())
memory = rows('memory.jsonl')
# A final sample may race with shutdown in the original collector.
while memory and memory[-1]['app_rss_kib'] is None:
    memory.pop()
if not memory or any(x.get('error') or x['app_rss_kib'] is None or not x['postgres_rss_kib'] or x['mem_available_kib'] is None for x in memory):
    raise SystemExit('missing memory samples')
if (a.run / 'phases.json').exists():
    phases = json.loads((a.run / 'phases.json').read_text())
    memory = [x for x in memory if phases['workload.jsonl']['start_ns'] <= x['monotonic_ns'] <= phases['quiet']['end_ns']]
    if not memory:
        raise SystemExit('missing workload/quiet memory samples')
result = {'startup_ms': ready['elapsed_ms'], 'memory_samples': len(memory),
          'note': 'Memory covers workload and quiet interval (startup-only runs cover startup); PostgreSQL summed RSS includes shared pages.'}
for name, values in [('app_rss_kib', [x['app_rss_kib'] for x in memory]),
                     ('postgres_sum_rss_kib', [sum(x['postgres_rss_kib'].values()) for x in memory]),
                     ('host_available_kib', [x['mem_available_kib'] for x in memory])]:
    result[name] = {'median': statistics.median(values), 'min': min(values), 'max': max(values)}
if (a.run / 'workload.jsonl').exists():
    requests = rows('workload.jsonl')
    if not requests or any(x['status'] != 200 or x['error'] for x in requests):
        raise SystemExit('missing or failed requests')
    result['paths'] = {}
    for path in dict.fromkeys(x['path'] for x in requests):
        group = [x for x in requests if x['path'] == path]
        values = [x['elapsed_ms'] for x in group]
        result['paths'][path] = {'count': len(group), 'median_ms': statistics.median(values),
                                 'min_ms': min(values), 'max_ms': max(values),
                                 'response_bytes': sorted({x['bytes'] for x in group})}
print(json.dumps(result, indent=2))
