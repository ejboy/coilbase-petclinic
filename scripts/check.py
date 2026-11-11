#!/usr/bin/env python3
"""Smoke the packaged application against a disposable, explicitly initialized H2 file."""
import html
import http.client
from html.parser import HTMLParser
from datetime import datetime, timezone
import http.cookiejar
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None

def client():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect())

def request(opener, base, path, data=None, headers=None):
    req = urllib.request.Request(base + path, data=None if data is None else urllib.parse.urlencode(data, doseq=True).encode(), headers=headers or {})
    try:
        with opener.open(req, timeout=3) as r: return r.status, r.headers, r.read().decode()
    except urllib.error.HTTPError as r: return r.code, r.headers, r.read().decode()

class Options(HTMLParser):
    def __init__(self):
        super().__init__(); self.options = []
    def handle_starttag(self, tag, attrs):
        if tag == 'option':
            attributes = dict(attrs)
            self.options.append((attributes.get('value'), 'selected' in attributes))

def selected(body):
    parser = Options(); parser.feed(body)
    return [value for value, is_selected in parser.options if is_selected]

def token(body): return re.search(r'name="_csrf" value="([^"]+)"', body).group(1)

def start(url, port, log_path):
    env = dict(os.environ, PETCLINIC_DB=url, PETCLINIC_SECURE_COOKIE='false', PORT=str(port))
    with log_path.open('w') as log:
        return subprocess.Popen(['java', '-jar', 'target/petclinic-1.0-SNAPSHOT.jar'], env=env, stdout=log, stderr=subprocess.STDOUT)

def ready(opener, base, process):
    for _ in range(600):
        if process.poll() is not None: raise AssertionError('application exited')
        try:
            if request(opener,base,'/owners/1/edit')[0] == 200: return
        except OSError: time.sleep(.1)
    raise AssertionError('application did not start')

def stop(process):
    process.terminate()
    try: process.wait(timeout=10)
    except subprocess.TimeoutExpired: process.kill(); process.wait()

results = Path('results') / ('phase-1-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
results.mkdir(parents=True)
print('Startup diagnostics:', results, flush=True)
with tempfile.TemporaryDirectory(prefix='petclinic-foundation-') as tmp:
    url = 'jdbc:h2:file:' + str(Path(tmp)/'db')
    h2 = next(Path('target/lib').glob('h2-*.jar'))
    for script in ('schema.sql','data.sql'):
        subprocess.run(['java','-cp',str(h2),'org.h2.tools.RunScript','-url',url,'-user','','-script',str(Path('src/test/resources')/script)],check=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    browser = client(); other = client(); process = start(url,port,results / 'startup-1.log')
    try:
        ready(client(),base,process)
        status, headers, body = request(browser,base,'/owners/1/edit')
        assert status == 200 and 'George' in body and 'lang="en"' in body
        assert 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Lax' in headers['Set-Cookie']
        csrf = token(body)
        assert request(browser,base,'/owners/find')[0] == 200
        assert 'has not been found' in request(browser,base,'/owners?lastName=NoSuchOwner')[2]
        status, headers, _ = request(browser,base,'/owners?lastName=Franklin')
        assert status == 302 and headers['Location'] == '/owners/1'
        status, _, listing = request(browser,base,'/owners?lastName=&page=1')
        assert status == 200 and '1 / 2' in listing
        assert '2 / 2' in request(browser,base,'/owners?lastName=&page=2')[2]
        assert request(browser,base,'/owners?lastName=&page=0')[0] == 302
        assert request(browser,base,'/owners?lastName=&page=oops')[0] == 400
        create = {'_csrf': csrf, 'firstName': 'PhaseThree', 'lastName': 'Created',
                  'address': '1 Test St', 'city': 'Madison', 'telephone': '6085551234'}
        status, _, invalid = request(browser,base,'/owners/new', {**create, 'telephone': 'bad'})
        assert status == 200 and 'telephone-error' in invalid and 'PhaseThree' in invalid
        assert 'has not been found' in request(browser,base,'/owners?lastName=Created')[2]
        status, headers, _ = request(browser,base,'/owners/new', create)
        assert status == 302 and re.fullmatch(r'/owners/\d+', headers['Location'])
        created_path = headers['Location']
        assert 'PhaseThree' in request(browser,base,created_path)[2]
        assert request(browser,base,'/owners/nope/edit')[0] == 400
        assert request(browser,base,'/owners/999999999999999999999/edit')[0] == 400
        assert request(browser,base,'/owners/-1/edit')[0] == 404
        assert request(browser,base,'/owners/1/edit', {'firstName':'Intruder'})[0] == 403
        malformed = urllib.request.Request(base + '/owners/1/edit', data=b'_csrf=%ZZ')
        try:
            browser.open(malformed, timeout=3)
            raise AssertionError('expected malformed form rejection')
        except urllib.error.HTTPError as response:
            assert response.code == 400

        request(other,base,'/owners/1/edit')
        assert request(other,base,'/owners/1/edit', {'_csrf':csrf,'firstName':'Intruder'})[0] == 403
        status, _, body = request(browser,base,'/owners/1/edit', {'_csrf':csrf,'firstName':'<script>"&','address':'','telephone':'bad'})
        assert status == 200 and 'address-error' in body and 'telephone-error' in body
        assert '<script>' not in body and '<script>"&' in html.unescape(body)
        owner2_before = request(browser,base,'/owners/2/edit')[2]
        for supplied in ('1', '2', 'xyz', ['1', '2']):
            status, headers, _ = request(browser,base,'/owners/1/edit', {'_csrf':csrf,'id':supplied,'firstName':'George'})
            assert status in (302,303) and headers['Location'] == '/owners/1'
        owner2_after = request(browser,base,'/owners/2/edit')[2]
        for value in ('Betty', 'Davis', '638 Cardinal Ave.', 'Sun Prairie', '6085551749'):
            assert value in owner2_before and value in owner2_after
        # Verify the exact limit is accepted and larger bodies are rejected.
        prefix = urllib.parse.urlencode({'_csrf': csrf, 'firstName': 'George', 'padding': ''}).encode()
        exact = prefix + b'x' * (16384 - len(prefix))
        fixed = urllib.request.Request(base + '/owners/1/edit', data=exact)
        try:
            browser.open(fixed, timeout=3)
            raise AssertionError('expected redirect for bounded body')
        except urllib.error.HTTPError as response:
            assert response.code in (302, 303)
        # Test actual fixed-length and transfer-coded bodies before any parsing.
        status, _, _ = request(browser,base,'/owners/1/edit', {'_csrf':csrf, 'firstName':'x' * 17000})
        assert status == 413
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        conn.request('POST', '/owners/1/edit', body=iter([b'_csrf=', csrf.encode(), b'&firstName=Intruder']), headers={'Content-Type':'application/x-www-form-urlencoded'}, encode_chunked=True)
        assert conn.getresponse().status == 411
        conn.close()
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        conn.request('POST', '/owners/1/edit', body=iter([b'x' * 20000]), headers={'Content-Type':'application/x-www-form-urlencoded'}, encode_chunked=True)
        assert conn.getresponse().status == 411
        conn.close()
        with socket.create_connection(('127.0.0.1',port), timeout=5) as raw:
            raw.sendall(b'POST /owners/1/edit HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
            response = raw.recv(4096)
            assert b' 411 ' in response.split(b'\r\n',1)[0], response
        assert 'George' in request(browser,base,'/owners/1/edit')[2]
        status, _, body = request(browser,base,'/owners/1/pets/new',headers={'Accept-Language':'es'})
        assert status == 200 and 'lang="es"' in body and 'Añadir mascota' in body
        assert selected(body) == []
        status, _, body = request(browser,base,'/owners/1/pets/new',{'_csrf':csrf,'name':'<b>x','birthDate':'nonsense','type':'999'}, {'Accept-Language':'es'})
        assert status == 200 and 'birthDate-error' in body and 'type-error' in body and '&lt;b>' in body
        status, _, body = request(browser,base,'/owners/1/pets/new',{'_csrf':csrf,'name':'Pet','birthDate':'nonsense','type':'dog'})
        assert status == 200 and 'birthDate-error' in body and selected(body) == ['dog']
        assert request(browser,base,'/owners/1/pets/new',{'_csrf':csrf,'name':'NewPet','birthDate':'2020-01-01','type':'cat'})[0] in (302,303)
        assert 'New Pet has been Added' in request(browser,base,'/owners/1')[2]
        assert 'New Pet has been Added' not in request(browser,base,'/owners/1')[2]
        assert request(browser,base,'/owners/1/edit',{'_csrf':csrf,'firstName':'Updated'})[0] in (302,303)
    finally: stop(process)
    process = start(url,port,results / 'startup-2.log')
    try:
        fresh = client(); ready(fresh,base,process)
        assert 'Updated' in request(fresh,base,'/owners/1/edit')[2]
        assert 'PhaseThree' in request(fresh,base,created_path)[2]
        csrf = token(request(fresh,base,'/owners/1/pets/new')[2])
        status,_,body = request(fresh,base,'/owners/1/pets/new',{'_csrf':csrf,'name':'NewPet','birthDate':'2020-01-01','type':'cat'})
        assert status == 200 and 'already exists' in body
        print('PASS: packaged forms, dropdown, IDs, body limits, CSRF, flash, locale and persistent restart')
    finally: stop(process)

    process = start(url, port, results / 'startup-3.log')
    try:
        ready(client(), base, process)
        print('PASS: 3 packaged launches; diagnostics retained in', results)
    finally:
        stop(process)
