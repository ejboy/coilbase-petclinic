#!/usr/bin/env python3
"""Verify shared contract writes remain visible after an application restart."""
import sys
import urllib.request

base = sys.argv[1]
with urllib.request.urlopen(base + '/owners/1', timeout=5) as response:
    assert response.status == 200
    body = response.read().decode()
    for expected in ('SharedOwner', 'LeoEdited', 'Shared visit + café', 'SharedPet'):
        assert expected in body, expected
with urllib.request.urlopen(base + '/owners?lastName=SharedCreated', timeout=5) as response:
    assert response.status == 200
    assert 'SharedNew' in response.read().decode()
print('PASS: shared writes visible after restart')
