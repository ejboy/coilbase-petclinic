#!/usr/bin/env python3
"""Exercise the same read-only PetClinic pages; emit per-request JSON lines."""
import argparse
import json
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('base', help='base URL of an independently initialized application')
parser.add_argument('--cycles', type=int, default=20)
args = parser.parse_args()
if args.cycles < 1:
    parser.error('cycles must be positive')
paths = ('/', '/owners/find', '/owners?lastName=Franklin', '/owners/1',
         '/owners/1/edit', '/owners/1/pets/new', '/vets.html', '/vets')
for cycle in range(args.cycles):
    for path in paths:
        started = time.monotonic_ns()
        status = None
        size = 0
        error = None
        try:
            with urllib.request.urlopen(args.base.rstrip('/') + path, timeout=10) as response:
                status = response.status
                body = response.read()
            size = len(body)
            marker = {'/owners?lastName=Franklin': b'Franklin', '/owners/1': b'Franklin',
                      '/owners/1/edit': b'Franklin', '/vets': b'vetList'}.get(path)
            if marker and marker not in body:
                error = 'expected content missing'
        except (OSError, urllib.error.HTTPError) as exc:
            status = getattr(exc, 'code', None)
            error = str(exc)
        print(json.dumps({'cycle': cycle + 1, 'path': path, 'status': status,
                          'bytes': size, 'elapsed_ms': (time.monotonic_ns() - started) / 1e6,
                          'error': error}), flush=True)
        if status != 200 or error:
            raise SystemExit('workload failed; retain partial output')
