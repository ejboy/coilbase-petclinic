#!/usr/bin/env python3
"""Run one fresh PetClinic JVM and capture readiness and quiet memory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('variant', choices=('spring-old', 'spring-current', 'spring-aot', 'coilbase', 'coilbase-aot'))
parser.add_argument('deploy', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--quiet-seconds', type=int, default=15)
parser.add_argument('--database', default='petclinic_aot_training')
args = parser.parse_args()
if os.geteuid() != 0:
    parser.error('run as root to read PostgreSQL PSS')
args.output.mkdir(parents=True, exist_ok=False)
deploy = args.deploy.resolve(strict=True)
password = os.environ['PETCLINIC_AOT_PASSWORD']
kind = 'coilbase' if args.variant.startswith('coilbase') else 'spring'
folder = deploy / ('coilbase' if kind == 'coilbase' else args.variant)
jar = folder / ('petclinic-1.0-SNAPSHOT.jar' if kind == 'coilbase' else 'spring-petclinic-4.0.0-SNAPSHOT.jar')
cache = folder / ('app-absolute.aot' if kind == 'spring' else 'app.aot')
optimized = args.variant in ('spring-aot', 'coilbase-aot')
command = ['java', '-Xms64m', '-Xmx256m', '-Xlog:gc']
if optimized:
    command += ['-XX:AOTMode=on', '-XX:AOTCache=' + str(cache), '-Xlog:aot']
if args.variant == 'spring-aot':
    command.append('-Dspring.aot.enabled=true')
command += ['-jar', str(jar)]
env = os.environ.copy()
jdbc = 'jdbc:postgresql://127.0.0.1:5432/' + args.database
if kind == 'spring':
    command += ['--server.port=8080', '--spring.datasource.url=' + jdbc,
                '--spring.datasource.username=petclinic_aot', '--spring.sql.init.mode=never']
    env['SPRING_DATASOURCE_PASSWORD'] = password
else:
    env.update(PORT='8080', PETCLINIC_DB=jdbc, PETCLINIC_DB_USER='petclinic_aot',
               PETCLINIC_DB_PASSWORD=password, PETCLINIC_SECURE_COOKIE='false')
(args.output / 'command.json').write_text(json.dumps(command, indent=2) + '\n')


def memory(pid):
    text = Path(f'/proc/{pid}/smaps_rollup').read_text()
    return {line.split(':')[0].lower() + '_kib': int(line.split()[1])
            for line in text.splitlines() if line.startswith(('Rss:', 'Pss:'))}


def sample(pid, phase):
    app = memory(pid)
    postgres = subprocess.check_output(['pgrep', '-x', 'postgres'], text=True).split()
    pg_pss = 0
    for pg_pid in postgres:
        try:
            pg_pss += memory(pg_pid)['pss_kib']
        except FileNotFoundError:
            continue
    available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    return {'phase': phase, 'monotonic_ns': time.monotonic_ns(), 'app': app,
            'postgres_pss_kib': pg_pss, 'mem_available_kib': available}


def get(path, expected=b''):
    with urllib.request.urlopen('http://127.0.0.1:8080' + path, timeout=2) as response:
        body = response.read()
        return response.status == 200 and expected in body


samples = []
with (args.output / 'application.log').open('w') as log:
    started = time.monotonic_ns()
    process = subprocess.Popen(command, cwd=folder, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        readiness = {}
        for name, path, expected in [('root', '/', b''), ('owner', '/owners/1', b'Franklin')]:
            deadline = time.monotonic() + 90
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f'application exited before {name} readiness')
                try:
                    if get(path, expected):
                        readiness[name + '_ms'] = (time.monotonic_ns() - started) / 1e6
                        break
                except (OSError, urllib.error.HTTPError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError(f'{name} readiness timed out')
                time.sleep(.1)
        samples.append(sample(process.pid, 'readiness'))
        for path in ('/', '/owners/find', '/owners/1', '/vets.html', '/vets'):
            if not get(path):
                raise RuntimeError(f'failed read {path}')
        quiet_start = time.monotonic()
        while time.monotonic() - quiet_start < args.quiet_seconds:
            samples.append(sample(process.pid, 'quiet'))
            time.sleep(1)
        if optimized:
            log.flush()
            log_text = (args.output / 'application.log').read_text(errors='replace')
            if f'Opened AOT cache {cache}.' not in log_text:
                raise RuntimeError('intended AOT cache was not opened')
            if kind == 'spring' and 'Starting AOT-processed' not in log_text:
                raise RuntimeError('Spring AOT startup was not observed')
        result = {'variant': args.variant, 'readiness': readiness, 'pid': process.pid,
                  'quiet_seconds': args.quiet_seconds, 'samples': samples}
        (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError('application did not shut down gracefully')
        (args.output / 'exit.json').write_text(json.dumps({'returncode': process.returncode}) + '\n')
