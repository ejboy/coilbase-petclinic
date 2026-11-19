#!/usr/bin/env python3
"""Validate and summarize three-round PetClinic startup observations."""
import json
from pathlib import Path
import statistics
import sys

root = Path(sys.argv[1])
spring_followup = Path(sys.argv[2]) if len(sys.argv) > 2 else root
variants = ('spring-old', 'spring-current', 'spring-aot', 'coilbase', 'coilbase-aot')
rows = {}
for variant in variants:
    observations = []
    for round_number in range(1, 4):
        source = spring_followup if variant == 'spring-aot' else root
        directory = source / f'r{round_number}-{variant}'
        result = json.loads((directory / 'result.json').read_text())
        exit_info = json.loads((directory / 'exit.json').read_text())
        assert result['variant'] == variant and exit_info['returncode'] == 143, directory
        quiet = [sample for sample in result['samples'] if sample['phase'] == 'quiet']
        assert len(quiet) >= 10 and result['quiet_seconds'] == 15, directory
        assert 0 < result['readiness']['root_ms'] <= result['readiness']['owner_ms'], directory
        assert all(s['app']['rss_kib'] >= s['app']['pss_kib'] > 0
                   and s['postgres_pss_kib'] > 0 and s['mem_available_kib'] > 0
                   for s in result['samples']), directory
        log = (directory / 'application-log.txt').read_text()
        assert 'Using Serial' in log, directory
        if variant in ('spring-aot', 'coilbase-aot'):
            assert 'Opened AOT cache ' in log and 'unrecoverable error' not in log, directory
        if variant == 'spring-aot':
            assert 'Starting AOT-processed' in log, directory
        first = result['samples'][0]
        assert first['phase'] == 'readiness'
        observation = {'root_s': result['readiness']['root_ms'] / 1000,
                       'owner_s': result['readiness']['owner_ms'] / 1000,
                       'ready_rss_mib': first['app']['rss_kib'] / 1024,
                       'ready_pss_mib': first['app']['pss_kib'] / 1024,
                       'quiet_rss_mib': statistics.median(s['app']['rss_kib'] for s in quiet) / 1024,
                       'quiet_pss_mib': statistics.median(s['app']['pss_kib'] for s in quiet) / 1024,
                       'quiet_postgres_pss_mib': statistics.median(s['postgres_pss_kib'] for s in quiet) / 1024,
                       'quiet_available_mib': statistics.median(s['mem_available_kib'] for s in quiet) / 1024,
                       'quiet_samples': len(quiet)}
        observations.append(observation)
    summaries = {}
    for key in observations[0]:
        values = [row[key] for row in observations]
        summaries[key] = {'median': statistics.median(values), 'min': min(values), 'max': max(values)}
    rows[variant] = {'runs': observations, 'summary': summaries}
print(json.dumps(rows, indent=2))
