#!/usr/bin/env python3
"""Shared real-HTTP expectations for the workflows available in both applications."""
import argparse
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, *args):
        return None
parser = argparse.ArgumentParser()
parser.add_argument('base')
parser.add_argument('implementation', choices=['spring', 'coilbase'])
args = parser.parse_args()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    NoRedirect())

def request(path, data=None, headers=None):
    raw = None if data is None else urllib.parse.urlencode(data, doseq=True).encode()
    req = urllib.request.Request(args.base.rstrip('/') + path, data=raw, headers=headers or {})
    try:
        response = client.open(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return (response.status, response.headers, response.read().decode())

def form(path):
    status, headers, body = request(path)
    assert status == 200 and headers['Content-Type'].startswith('text/html'), (path, status)
    match = re.search('name="_csrf"\\s+value="([^"]+)"', body)
    return {'_csrf': match.group(1)} if args.implementation == 'coilbase' else {}

def post(path, values, status, target=None):
    token = form(path)
    actual, headers, body = request(path, {**values, **token})
    assert actual == status, (path, actual, status, body[:500])
    if target:
        assert urllib.parse.urlsplit(headers['Location']).path.split(';')[0] == target, headers['Location']
    return body
status, headers, body = request('/')
assert status == 200 and 'Welcome' in body and '/owners/find' in body and '/vets.html' in body
status, headers, body = request('/vets.html')
assert status == 200 and 'Veterinarians' in body and 'Carter' in body
status, _, second_page = request('/vets.html?page=2')
assert status == 200 and 'Jenkins' in second_page and 'Carter' not in second_page
assert request('/vets.html?page=0')[0] == 302
assert request('/vets.html?page=999')[0] == 302
status, headers, body = request('/vets')
assert status == 200 and headers.get('Content-Type', '').startswith('application/json')
vets = json.loads(body)['vetList']
assert len(vets) == 6
vets_by_name = {v['lastName']: v for v in vets}
assert sorted(s['name'] for s in vets_by_name['Douglas']['specialties']) == ['dentistry', 'surgery']
assert vets_by_name['Carter']['specialties'] == []
assert vets_by_name['Douglas']['nrOfSpecialties'] == 2 and vets_by_name['Douglas']['new'] is False
assert all(set(specialty) == {'id', 'name', 'new'} and specialty['new'] is False
           for specialty in vets_by_name['Douglas']['specialties'])
status, headers, css = request('/resources/css/petclinic.css')
assert status == 200 and 'text/css' in headers.get('Content-Type', '') and len(css) > 100
with client.open(args.base.rstrip('/') + '/resources/images/pets.png', timeout=15) as image:
    assert image.status == 200 and image.headers.get('Content-Type', '').startswith('image/png')
    assert image.read(8) == b'\x89PNG\r\n\x1a\n'
if args.implementation == 'coilbase':
    status, _, spanish = request('/vets.html', headers={'Accept-Language': 'es'})
    assert status == 200 and 'lang="es"' in spanish and 'Veterinarios' in spanish
    _, _, fallback = request('/vets.html', headers={'Accept-Language': 'xx'})
    assert 'lang="en"' in fallback and 'Veterinarians' in fallback
    assert request('/resources/images/no-such-image.png')[0] == 404
    assert request('/oups')[0] == 500
    assert request('/no-such-route')[0] == 404
assert request('/owners/find')[0] == 200
assert request('/owners?lastName=NoSuchOwner')[0] == 200
status, headers, _ = request('/owners?lastName=Franklin')
assert status == 302 and urllib.parse.urlsplit(headers['Location']).path.split(';')[0] == '/owners/1'
assert request('/owners?lastName=&page=1')[0] == 200
assert request('/owners?lastName=&page=2')[0] == 200
assert request('/owners?lastName=&page=999')[0] == 302
new_owner = {'firstName': 'SharedNew', 'lastName': 'SharedCreated', 'address': '1 Test St',
             'city': 'Madison', 'telephone': '6085551234'}
assert 'SharedNew' in post('/owners/new', {**new_owner, 'telephone': 'bad'}, 200)
status, headers, _ = request('/owners/new', {**new_owner, **form('/owners/new')})
assert status == 302
new_path = urllib.parse.urlsplit(headers['Location']).path.split(';')[0]
assert re.fullmatch(r'/owners/\d+', new_path)
assert 'New Owner Created' in request(new_path)[2]
owner = {'firstName': 'SharedOwner',
    'lastName': 'Franklin',
    'address': '110 W. Liberty St.',
    'city': 'Madison',
    'telephone': '6085551023'}
body = post('/owners/1/edit', {**owner, 'telephone': 'bad'}, 200)
assert 'SharedOwner' in body
assert 'SharedOwner' not in request('/owners/1')[2]
post('/owners/1/edit', owner, 302, '/owners/1')
status, _, body = request('/owners/1')
assert status == 200 and 'SharedOwner' in body and ('Owner Values Updated' in body)
assert 'Owner Values Updated' not in request('/owners/1')[2]
pet = {'name': 'SharedPet', 'birthDate': '2020-01-01', 'type': 'cat'}
post('/owners/1/pets/new', {**pet, 'birthDate': 'invalid'}, 200)
post('/owners/1/pets/new', pet, 302, '/owners/1')
assert 'New Pet has been Added' in request('/owners/1')[2]
post('/owners/1/pets/new', pet, 200)
edit_path = '/owners/1/pets/1/edit'
assert 'Leo' in request(edit_path)[2]
assert 'LeoEdited' in post(edit_path, {'name': 'LeoEdited', 'birthDate': 'bad', 'type': 'cat'}, 200)
post(edit_path, {'name': 'LeoEdited', 'birthDate': '2020-01-01', 'type': 'invalid'}, 200)
assert 'LeoEdited' not in request('/owners/1')[2]
post(edit_path, {'name': 'LeoEdited', 'birthDate': '2020-01-01', 'type': 'cat', 'id': '8'}, 302, '/owners/1')
assert 'LeoEdited' in request('/owners/1')[2]
post(edit_path, {'name': 'SharedPet', 'birthDate': '2020-01-01', 'type': 'cat'}, 200)
visit_path = '/owners/1/pets/1/visits/new'
assert 'LeoEdited' in request(visit_path)[2]
post(visit_path, {'date': '2000-01-01', 'description': 'Invalid shared visit'}, 200)
post(visit_path, {'date': '2099-01-01', 'description': ''}, 200)
post(visit_path, {'date': '2099-01-01', 'description': 'Shared visit + café', 'petId': '8'}, 302, '/owners/1')
status, _, detail = request('/owners/1')
assert 'Shared visit + café' in detail, (status, detail)
post(visit_path, {'date': '2098-01-01', 'description': 'Earlier shared visit'}, 302, '/owners/1')
detail = request('/owners/1')[2]
assert detail.index('Earlier shared visit') < detail.index('Shared visit + café')
assert request('/owners/nope/edit')[0] == 400
if args.implementation == 'coilbase':
    assert request('/owners/1/edit', owner)[0] == 403
    assert request('/owners/2/pets/1/edit')[0] == 404
    assert request('/owners/2/pets/1/visits/new')[0] == 404
    assert request('/owners/1/pets/nope/edit')[0] == 400
    assert request('/owners/1/pets/999999999999999999999/visits/new')[0] == 400
    csrf = form(edit_path)
    assert request('/owners/2/pets/1/edit', {**pet, **csrf})[0] == 404
    assert request('/owners/2/pets/1/visits/new', {'date': '2099-01-01', 'description': 'wrong owner', **csrf})[0] == 404
    assert request(visit_path, {'date': '2099-01-01', 'description': 'no csrf'})[0] == 403
print('PASS: shared owner and pet HTTP contract on', args.implementation)
