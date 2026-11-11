#!/usr/bin/env python3
"""Run contract checks on isolated fresh H2 files, then inspect committed rows."""
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
import zipfile

HERE = Path(__file__).resolve().parent
APP = HERE.parent
parser = argparse.ArgumentParser()
parser.add_argument(
    '--spring-jar', type=Path, required=True,
    help='JAR built from the pinned revision in a separate checkout',
)
args = parser.parse_args()
spring_jar = args.spring_jar.resolve()
coil_jar = APP / 'target/petclinic-1.0-SNAPSHOT.jar'
coil_h2 = next((APP / 'target/lib').glob('h2-*.jar'))


def java(*args):
    result = subprocess.run(
        ['java', *map(str, args)], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return result.stdout


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def run_process(kind, jar, url, checks, log, initialize=True):
    chosen = port()
    env = dict(os.environ)
    command = ['java', '-jar', str(jar)]
    if kind == 'spring':
        command += [
            f'--server.port={chosen}', f'--spring.datasource.url={url}',
            '--spring.sql.init.mode=' + ('always' if initialize else 'never'),
        ]
    else:
        env.update(PORT=str(chosen), PETCLINIC_DB=url, PETCLINIC_SECURE_COOKIE='false')
    with open(log, 'w') as output:
        process = subprocess.Popen(command, cwd=APP, env=env, stdout=output, stderr=subprocess.STDOUT)
        try:
            base = f'http://127.0.0.1:{chosen}'
            ready_path = '/' if kind == 'spring' else '/owners/1/edit'
            for _ in range(300):
                if process.poll() is not None:
                    raise RuntimeError(f'{kind} exited during startup')
                try:
                    with urllib.request.urlopen(base + ready_path, timeout=1):
                        break
                except (OSError, urllib.error.HTTPError):
                    time.sleep(0.1)
            else:
                raise RuntimeError(f'{kind} startup timed out')
            for check in checks:
                subprocess.run([sys.executable, str(HERE / check[0]), base, *check[1:]], check=True)
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def inspect(jar, url, statements):
    for sql, expected in statements:
        result = java(
            '-cp', jar, 'org.h2.tools.Shell', '-url', url,
            '-user', '', '-password', '', '-sql', sql,
        )
        assert expected in [line.strip() for line in result.splitlines()], (sql, expected, result)


with tempfile.TemporaryDirectory(prefix='petclinic-contract-') as directory:
    tmp = Path(directory)
    try:
        with zipfile.ZipFile(spring_jar) as archive:
            h2_entry = next(
                name for name in archive.namelist()
                if name.startswith('BOOT-INF/lib/h2-') and name.endswith('.jar')
            )
            spring_h2 = tmp / 'spring-h2.jar'
            spring_h2.write_bytes(archive.read(h2_entry))
        spring_url = 'jdbc:h2:file:' + str(tmp / 'spring')
        coil_url = 'jdbc:h2:file:' + str(tmp / 'coil')
        for fixture in ('schema.sql', 'data.sql'):
            java(
                '-cp', coil_h2, 'org.h2.tools.RunScript', '-url', coil_url,
                '-user', '', '-script', APP / 'src/test/resources' / fixture,
            )
        run_process('spring', spring_jar, spring_url,
                    [('check.py',), ('shared.py', 'spring')], tmp / 'spring.log')
        run_process('coilbase', coil_jar, coil_url,
                    [('shared.py', 'coilbase'), ('coil-flash.py',)], tmp / 'coil.log')
        inspect(spring_h2, spring_url, [
            ('select first_name from owners where id=1', 'SharedOwner'),
            ("select count(*) from owners where first_name='SharedNew' and last_name='SharedCreated'", '1'),
            ("select count(*) from pets where id=1 and owner_id=1 and name='LeoEdited'", '1'),
            ("select count(*) from visits where pet_id=1 and description='Shared visit + café'", '1'),
            ("select count(*) from visits where description in ('Invalid shared visit','wrong owner','no csrf')", '0'),
            ("select count(*) from pets where owner_id=1 and name in ('SharedPet','ContractPet')", '2'),
            ("select count(*) from visits where pet_id=1 and description='Contract visit'", '1'),
            ("select count(*) from owners where first_name='ContractNew'", '1'),
            ("select count(*) from pets where name='InvalidPet'", '0'),
            ("select count(*) from visits where description='Invalid visit'", '0'),
        ])
        inspect(coil_h2, coil_url, [
            ('select first_name from owners where id=1', 'SharedOwner'),
            ("select count(*) from owners where first_name='SharedNew' and last_name='SharedCreated'", '1'),
            ("select count(*) from pets where id=1 and owner_id=1 and name='LeoEdited'", '1'),
            ("select count(*) from visits where pet_id=1 and description='Shared visit + café'", '1'),
            ("select count(*) from visits where description in ('Invalid shared visit','wrong owner','no csrf')", '0'),
            ("select count(*) from pets where owner_id=1 and name='SharedPet'", '1'),
        ])
        print('PASS: independent committed H2 rows for Spring and CoilBase')
        run_process('spring', spring_jar, spring_url, [('restart.py',)], tmp / 'spring-restart.log', initialize=False)
        run_process('coilbase', coil_jar, coil_url, [('restart.py',)], tmp / 'coil-restart.log', initialize=False)
    except Exception:
        for log in (tmp / 'spring.log', tmp / 'coil.log', tmp / 'spring-restart.log', tmp / 'coil-restart.log'):
            if log.exists():
                print(f'\n--- {log.name} ---', file=sys.stderr)
                print(log.read_text(errors='replace'), file=sys.stderr)
        raise
