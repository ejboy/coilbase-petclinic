#!/usr/bin/env python3
"""Guest-side serial PetClinic measurement; inputs must be prepared first."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('kind', choices=('spring', 'coilbase'))
p.add_argument('jar', type=Path)
p.add_argument('jdbc_url')
p.add_argument('output', type=Path, help='new output directory')
p.add_argument('--user', default='petclinic')
p.add_argument('--cycles', type=int, default=20)
p.add_argument('--quiet-seconds', type=int, default=10)
p.add_argument('--startup-only', action='store_true')
p.add_argument('--ready-path', default='/', help='HTTP path used for readiness')
p.add_argument('--ready-contains', default='', help='required UTF-8 response text')
a = p.parse_args()
if not a.ready_path.startswith('/') or a.ready_path.startswith('//'):
    p.error('ready-path must be an absolute local path')
if a.cycles < 1 or a.quiet_seconds < 1:
    p.error('cycles and quiet-seconds must be positive')
password = os.environ.get('PETCLINIC_PERF_PASSWORD')
if password is None:
    p.error('set PETCLINIC_PERF_PASSWORD')
a.output.mkdir(parents=True, exist_ok=False)
jar = a.jar.resolve(strict=True)
env = os.environ.copy()
command = ['java', '-Xms64m', '-Xmx256m', '-Xlog:gc', '-jar', str(jar)]
if a.kind == 'spring':
    command += ['--server.port=8080', '--spring.datasource.url=' + a.jdbc_url,
                '--spring.datasource.username=' + a.user, '--spring.sql.init.mode=never']
    env['SPRING_DATASOURCE_PASSWORD'] = password
else:
    env.update(PORT='8080', PETCLINIC_DB=a.jdbc_url, PETCLINIC_DB_USER=a.user,
               PETCLINIC_DB_PASSWORD=password, PETCLINIC_SECURE_COOKIE='false')
(a.output / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
stop = threading.Event()

def sample(pid):
    with (a.output / 'memory.jsonl').open('w') as output:
        while not stop.is_set():
            row = {'wall_time_ns': time.time_ns(), 'monotonic_ns': time.monotonic_ns(),
                   'app_pid': pid, 'app_rss_kib': None, 'postgres_rss_kib': {},
                   'mem_available_kib': None}
            try:
                for line in Path(f'/proc/{pid}/status').read_text().splitlines():
                    if line.startswith('VmRSS:'):
                        row['app_rss_kib'] = int(line.split()[1])
                for line in Path('/proc/meminfo').read_text().splitlines():
                    if line.startswith('MemAvailable:'):
                        row['mem_available_kib'] = int(line.split()[1])
                ps = subprocess.run(['ps', '-C', 'postgres', '-o', 'pid=', '-o', 'rss='],
                                    text=True, capture_output=True, check=False)
                for line in ps.stdout.splitlines():
                    process, rss = line.split()
                    row['postgres_rss_kib'][process] = int(rss)
            except (OSError, ValueError) as exc:
                row['error'] = str(exc)
            output.write(json.dumps(row) + '\n')
            output.flush()
            stop.wait(1)

with (a.output / 'application.log').open('w') as log:
    started = time.monotonic_ns()
    process = subprocess.Popen(command, cwd=jar.parent, env=env, stdout=log, stderr=subprocess.STDOUT)
    sampler = threading.Thread(target=sample, args=(process.pid,))
    sampler.start()
    try:
        deadline = time.monotonic() + 90
        while True:
            if process.poll() is not None:
                raise RuntimeError(f'application exited: {process.returncode}')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8080' + a.ready_path, timeout=2) as response:
                    if response.status == 200:
                        body = response.read()
                        if a.ready_contains.encode('utf-8') in body:
                            break
            except (OSError, urllib.error.HTTPError):
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError('readiness timed out')
            time.sleep(.1)
        (a.output / 'readiness.json').write_text(json.dumps({
            'pid': process.pid, 'elapsed_ms': (time.monotonic_ns() - started) / 1e6,
            'ready_wall_time_ns': time.time_ns(), 'poll_interval_seconds': .1,
            'path': a.ready_path, 'required_text': a.ready_contains}, indent=2) + '\n')
        if not a.startup_only:
            phases = {}
            for name, cycles in [('warmup.jsonl', 1), ('workload.jsonl', a.cycles)]:
                phases[name] = {'start_ns': time.monotonic_ns()}
                with (a.output / name).open('w') as out:
                    subprocess.run([sys.executable, str(HERE / 'workload.py'),
                                    'http://127.0.0.1:8080', '--cycles', str(cycles)],
                                   stdout=out, check=True)
                phases[name]['end_ns'] = time.monotonic_ns()
            phases['quiet'] = {'start_ns': time.monotonic_ns()}
            time.sleep(a.quiet_seconds)
            phases['quiet']['end_ns'] = time.monotonic_ns()
            (a.output / 'phases.json').write_text(json.dumps(phases, indent=2) + '\n')
    finally:
        stop.set()
        sampler.join()
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        (a.output / 'exit.json').write_text(json.dumps({'returncode': process.returncode}) + '\n')
