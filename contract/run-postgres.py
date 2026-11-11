#!/usr/bin/env python3
"""Run the shared contract in two isolated PostgreSQL schemas.

The databases must be disposable and distinct. The supplied user needs CREATE
on both databases. PGPASSWORD supplies the password without a command argument.
"""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
APP = HERE.parent
FIXTURES = APP / 'src/test/resources/postgres'
parser = argparse.ArgumentParser()
parser.add_argument('--spring-jar', type=Path, required=True)
parser.add_argument('--spring-db', required=True, help='PostgreSQL connection URI')
parser.add_argument('--coil-db', required=True, help='different PostgreSQL connection URI')
args = parser.parse_args()
if args.spring_db == args.coil_db:
    parser.error('supply two distinct database URIs')
if not os.environ.get('PGUSER') or not os.environ.get('PGPASSWORD'):
    parser.error('set PGUSER and PGPASSWORD')


def psql(uri, *options, input=None):
    result = subprocess.run(['psql', '-X', '-q', '-v', 'ON_ERROR_STOP=1', '-d', uri, *options],
                            input=input, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'psql failed: {result.stderr.strip()}')
    return result.stdout


def jdbc(uri, schema):
    if not uri.startswith('postgresql://') or '?' in uri or '@' in uri:
        raise ValueError('database URIs must be postgresql://host:port/database without credentials or options')
    return 'jdbc:' + uri + '?currentSchema=' + schema


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def run(kind, uri, schema, log, restart=False):
    port = free_port()
    url = jdbc(uri, schema)
    env = dict(os.environ)
    user = env.get('PGUSER', '')
    if kind == 'spring':
        command = ['java', '-jar', str(args.spring_jar.resolve()), f'--server.port={port}',
                   f'--spring.datasource.url={url}', f'--spring.datasource.username={user}',
                   '--spring.sql.init.mode=never']
        env['SPRING_DATASOURCE_PASSWORD'] = env['PGPASSWORD']
    else:
        command = ['java', '-jar', str(APP / 'target/petclinic-1.0-SNAPSHOT.jar')]
        env.update(PORT=str(port), PETCLINIC_DB=url, PETCLINIC_DB_USER=user,
                   PETCLINIC_DB_PASSWORD=env['PGPASSWORD'], PETCLINIC_SECURE_COOKIE='false')
    with log.open('w') as output:
        process = subprocess.Popen(command, cwd=APP, env=env, stdout=output, stderr=subprocess.STDOUT)
        try:
            base = f'http://127.0.0.1:{port}'
            for _ in range(300):
                if process.poll() is not None:
                    raise RuntimeError(f'{kind} exited during startup')
                try:
                    with urllib.request.urlopen(base + '/', timeout=1):
                        break
                except (OSError, urllib.error.HTTPError):
                    time.sleep(.1)
            else:
                raise RuntimeError(f'{kind} startup timed out')
            check = ['restart.py'] if restart else ['shared.py', kind]
            subprocess.run([sys.executable, str(HERE / check[0]), base, *check[1:]], check=True)
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


schemas = []
with tempfile.TemporaryDirectory(prefix='petclinic-pg-contract-') as directory:
    try:
        for uri in (args.spring_db, args.coil_db):
            schema = 'petclinic_contract_' + uuid.uuid4().hex
            psql(uri, '-c', f'CREATE SCHEMA {schema}')
            schemas.append((uri, schema))
            fixture = '\n'.join((FIXTURES / name).read_text() for name in ('schema.sql', 'data.sql'))
            psql(uri, input=f'SET search_path TO {schema};\n' + fixture)
        for (kind, (uri, schema)) in zip(('spring', 'coilbase'), schemas):
            log = Path(directory) / (kind + '.log')
            try:
                run(kind, uri, schema, log)
            except Exception:
                if log.exists():
                    print(log.read_text(errors='replace'), file=sys.stderr)
                raise
            result = psql(uri, '-At', '-c', f"""SET search_path TO {schema};
                SELECT (SELECT first_name FROM owners WHERE id=1),
                  (SELECT count(*) FROM owners WHERE first_name='SharedNew' AND last_name='SharedCreated'),
                  (SELECT count(*) FROM pets WHERE id=1 AND owner_id=1 AND name='LeoEdited'),
                  (SELECT count(*) FROM visits WHERE pet_id=1 AND description='Shared visit + café'),
                  (SELECT count(*) FROM visits WHERE description IN ('Invalid shared visit','wrong owner','no csrf')),
                  (SELECT count(*) FROM pets WHERE owner_id=1 AND name='SharedPet');""").strip()
            assert result == 'SharedOwner|1|1|1|0|1', (kind, result)
            print(f'PASS: independent PostgreSQL committed rows on {kind}')
            restart_log = Path(directory) / (kind + '-restart.log')
            try:
                run(kind, uri, schema, restart_log, restart=True)
            except Exception:
                if restart_log.exists():
                    print(restart_log.read_text(errors='replace'), file=sys.stderr)
                raise
    finally:
        failed = sys.exc_info()[0] is not None
        cleanup_failed = False
        for uri, schema in schemas:
            try:
                psql(uri, '-c', f'DROP SCHEMA {schema} CASCADE')
            except Exception as error:
                cleanup_failed = True
                print(f'Could not remove test schema {schema} on {uri}: {error}', file=sys.stderr)
        if cleanup_failed and not failed:
            raise RuntimeError('test schema cleanup failed')
