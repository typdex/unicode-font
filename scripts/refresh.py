#!/usr/bin/env python3
"""Fetch pinned inputs, verify hashes, and extract font cmap evidence.

Normal runs require the checked-in lock. --update-lock explicitly accepts new bytes.
No fonts are installed and archives are read in memory, never extracted to disk.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import tarfile
import time
from urllib.request import Request, urlopen
import zipfile

from fontTools import version as fonttools_version
from fontTools.ttLib import TTFont, TTCollection

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_catalog import compact_ranges


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch(source, locked, update, rescan_local=False):
    cache = ROOT / '.cache' / (hashlib.sha256(source['url'].encode()).hexdigest())
    expected = locked.get(source['id'], {}).get('sha256')
    if source['kind'] == 'local-font' and not rescan_local:
        if not expected or locked[source['id']]['url'] != source['url']:
            raise ValueError('Local input needs --rescan-local: ' + source['id'])
        return source, None, locked[source['id']]
    if not update and not expected:
        raise ValueError('Input is not locked: ' + source['id'])
    if source['kind'] == 'local-font':
        path = Path(source['path'])
        data = (path if path.is_absolute() else ROOT / path).read_bytes()
    elif cache.exists():
        data = cache.read_bytes()
    else:
        for attempt in range(3):
            try:
                req = Request(source['url'], headers={'User-Agent': 'unicode-font-catalog/1.0'})
                with urlopen(req, timeout=90) as response:
                    data = response.read()
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
    actual = digest(data)
    if not update and (actual != expected or locked[source['id']]['url'] != source['url']):
        raise ValueError('Input changed; remove cache and investigate: ' + source['id'])
    return source, data, {'id': source['id'], 'url': source['url'],
                          'sha256': actual, 'bytes': len(data)}


def scan_font(data, source, member=None, face_index=None):
    with TTFont(BytesIO(data), lazy=True, fontNumber=face_index if face_index is not None else -1) as font:
        # Union ordinary Unicode cmaps. Format 14 describes sequences, not scalars.
        points = {cp for table in font['cmap'].tables
                  if table.isUnicode() and table.format != 14
                  for cp, glyph in table.cmap.items()
                  if 0 <= cp <= 0x10FFFF and not 0xD800 <= cp <= 0xDFFF
                  and font.getGlyphID(glyph) != 0}
        return {'id': source['id'] + ('::' + member if member else '') +
                      (f'::face-{face_index}' if face_index is not None else ''),
                'project': source['project'], 'source_id': source['id'],
                'member': member, 'face_index': face_index, 'family': font['name'].getDebugName(1),
                'style': font['name'].getDebugName(2),
                'version': font['name'].getDebugName(5),
                'embedded_license': font['name'].getDebugName(13),
                'embedded_license_url': font['name'].getDebugName(14),
                'sha256': digest(data), 'mapped_count': len(points),
                'mapped_ranges': compact_ranges(points)}


def scan_bytes(data, source, member=None):
    if data[:4] == b'ttcf':
        with TTCollection(BytesIO(data), lazy=True) as collection:
            count = len(collection.fonts)
        return [scan_font(data, source, member, face) for face in range(count)]
    return [scan_font(data, source, member)]


def scan(source, data):
    kind = source['kind']
    if kind in ('font', 'local-font'):
        return scan_bytes(data, source)
    if kind in ('zip', 'tar'):
        if kind == 'zip':
            with zipfile.ZipFile(BytesIO(data)) as archive:
                return [f for n in sorted(archive.namelist()) if n.lower().endswith(('.ttf', '.otf', '.ttc', '.otc'))
                        for f in scan_bytes(archive.read(n), source, n)]
        with tarfile.open(fileobj=BytesIO(data)) as archive:
            return [f
                    for m in sorted(archive.getmembers(), key=lambda m: m.name)
                    if m.isfile() and m.name.lower().endswith(('.ttf', '.otf', '.ttc', '.otc'))
                    for f in scan_bytes(archive.extractfile(m).read(), source, m.name)]
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update-lock', action='store_true')
    parser.add_argument('--rescan-local', action='store_true', help='remeasure local licensed or experimental font files')
    parser.add_argument('--local-project', action='append', help='limit --rescan-local to a project ID; repeatable')
    args = parser.parse_args()
    if args.local_project and not args.rescan_local:
        parser.error('--local-project requires --rescan-local')
    sources = json.loads((ROOT / 'catalog/sources.json').read_text())
    if len({s['id'] for s in sources['inputs']}) != len(sources['inputs']):
        raise ValueError('Duplicate source IDs')
    lock_path = ROOT / 'data/inputs.lock.json'
    old = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    locked = {s['id']: s for s in old.get('inputs', [])}
    previous_path = ROOT / 'data/font-coverage.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {'fonts': []}
    # Collect all inputs before replacing any checked-in evidence.
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda s: fetch(s, locked, args.update_lock,
            args.rescan_local and (not args.local_project or s.get('project') in args.local_project)), sources['inputs']))
    fonts, ucd_files = [], []
    for source, data, _ in results:
        if source['kind'] == 'ucd':
            ucd_files.append((source['filename'], data))
        else:
            scanned = (scan(source, data) if data is not None else
                       [f for f in previous['fonts'] if f['source_id'] == source['id']])
            if not scanned:
                raise ValueError('No font files in input: ' + source['id'])
            fonts.extend(scanned)
    if not fonts:
        raise ValueError('No fonts scanned')
    if len({f['id'] for f in fonts}) != len(fonts):
        raise ValueError('Duplicate font IDs')
    evidence = {'unicode_version': sources['unicode_version'],
                'fonttools_version': fonttools_version,
                'method': 'union of Unicode cmap mappings to nonzero glyph IDs; no format 14 sequences',
                'fonts': sorted(fonts, key=lambda f: f['id'])}
    for filename, data in ucd_files:
        destination = ROOT / 'data/ucd' / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (ROOT / 'data/font-coverage.json').write_text(json.dumps(evidence, indent=2) + '\n')
    if args.update_lock:
        lock = {'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'inputs': [entry for _, _, entry in results]}
        lock_path.write_text(json.dumps(lock, indent=2) + '\n')
    print(f'Verified {len(results)} inputs; scanned {len(fonts)} fonts.')


if __name__ == '__main__':
    main()
