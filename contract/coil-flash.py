#!/usr/bin/env python3
"""Check the accepted flash behavior difference on a disposable CoilBase fixture."""
import http.cookiejar
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, *args):
        return None
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    NoRedirect())
base = sys.argv[1].rstrip('/')

def request(path, data=None):
    req = urllib.request.Request(base + path,
        data=None if data is None else urllib.parse.urlencode(data).encode())
    try:
        response = client.open(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return (response.status, response.read().decode())

def update():
    status, body = request('/owners/1/edit')
    assert status == 200
    csrf = re.search('name="_csrf" value="([^"]+)"', body).group(1)
    assert request('/owners/1/edit', {'_csrf': csrf})[0] == 302

def check_other(path):
    update()
    status, other = request(path)
    assert status == 200 and 'Owner Values Updated' in other, path
    status, target = request('/owners/1')
    assert status == 200 and 'Owner Values Updated' not in target, path
check_other('/owners/2')
check_other('/owners/1/edit')
print('PASS: documented CoilBase flash discrepancy on owner detail and edit')
