#!/usr/bin/env python3
"""Representative Spring HTTP contract; run against a fresh pinned fixture only."""
import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
import sys

class NoRedirect(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, *args):
        return None
base = sys.argv[1].rstrip('/')
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    NoRedirect())

def request(path, data=None):
    req = urllib.request.Request(base + path,
        data=urllib.parse.urlencode(data).encode() if data is not None else None)
    try:
        response = client.open(req, timeout=15)
    except urllib.error.HTTPError as err:
        response = err
    with response:
        return (response.status, response.headers, response.read().decode())

def get(path, status=200, contains=None, content='text/html'):
    actual, headers, body = request(path)
    assert actual == status, (path, actual, status)
    if content:
        assert headers.get('Content-Type', '').startswith(content), (path, headers)
    if contains:
        assert contains in body, (path, contains)
    return body

def post(path, data, status=302, target='/owners/1'):
    actual, headers, body = request(path, data)
    assert actual == status, (path, actual, status, body[:500])
    if target:
        assert urllib.parse.urlsplit(headers['Location']).path.split(';')[0] == target, headers
    return body
get('/', contains='Welcome')
get('/owners/find')
spanish = get('/owners/1/edit?lang=es', contains='Propietario')
assert 'Nombre' in spanish
assert 'Propietario' in get('/owners/1/edit')
get('/owners/1/edit?lang=en', contains='Owner')
get('/owners/new', contains='firstName')
new_owner = {'firstName': 'ContractNew',
    'lastName': 'Person',
    'address': '1 Test St',
    'city': 'Madison',
    'telephone': '6085550000'}
post('/owners/new', dict(new_owner, telephone='bad'), 200, None)
status, headers, body = request('/owners/new', new_owner)
assert status == 302, (status, body[:500])
new_path = urllib.parse.urlsplit(headers['Location']).path.split(';')[0]
assert new_path.startswith('/owners/')
get(new_path, contains='ContractNew')
get('/owners', contains='Franklin')
status, headers, _ = request('/owners?lastName=Franklin')
assert status == 302 and urllib.parse.urlsplit(headers['Location']).path == '/owners/1'
get('/owners?lastName=NoSuchName')
status, headers, _ = request('/owners?page=0')
assert status == 302 and urllib.parse.urlsplit(headers['Location']).query == 'page=1'
get('/owners/nope/edit', 400, content='application/json')
get('/owners/-1/edit', 500, content='application/json')
get('/no-such-route', 404, content='application/json')
get('/owners/1', contains='George')
get('/owners/1/edit', contains='Franklin')
get('/owners/1/pets/new')
get('/owners/1/pets/1/edit', contains='Leo')
get('/owners/1/pets/1/visits/new', contains='Leo')
get('/vets.html', contains='Carter')
status, headers, body = request('/vets.html?page=0')
assert status == 302 and urllib.parse.urlsplit(headers['Location']).query == 'page=1'
status, headers, body = request('/vets')
assert status == 200 and headers['Content-Type'].startswith('application/json')
assert 'vetList' in json.loads(body) and 'Carter' in body
owner = {'firstName': 'ContractGeorge',
    'lastName': 'Franklin',
    'address': '110 W. Liberty St.',
    'city': 'Madison',
    'telephone': '6085551023'}
post('/owners/1/edit', dict(owner, telephone='bad'), 200, None)
assert 'ContractGeorge' not in get('/owners/1')
post('/owners/1/edit', owner)
assert 'Owner Values Updated' not in get('/owners/1/edit')
assert 'Owner Values Updated' not in get('/owners/2')
assert 'Owner Values Updated' in get('/owners/1', contains='ContractGeorge')
assert 'Owner Values Updated' not in get('/owners/1')
post('/owners/1/pets/new', {'name': 'InvalidPet', 'birthDate': 'invalid', 'type': 'cat'}, 200, None)
post('/owners/1/pets/1/visits/new', {'date': '2000-01-01', 'description': 'Invalid visit'}, 200, None)
post('/owners/1/pets/1/visits/new', {'date': '2099-01-01', 'description': ''}, 200, None)
post('/owners/1/pets/new', {'name': 'ContractPet', 'birthDate': '2020-01-01', 'type': 'cat'})
get('/owners/1', contains='ContractPet')
post('/owners/1/pets/1/visits/new', {'date': '2099-01-01', 'description': 'Contract visit'})
get('/owners/1', contains='Contract visit')
print('PASS: pinned Spring representative HTTP and state contract')
