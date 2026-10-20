#!/usr/bin/env python3
"""Incrementally build Typdex Jigmo U18 from the CC0 release and GlyphWiki SVGs.

This preserves every published glyph, cmap and variation sequence. It adds
Unicode 18 East Asian characters and optional explicit scalar code points;
it does not claim to cover every script in Unicode 18. Missing/empty SVGs are
recorded and never replaced by diagnostic glyphs. No FontForge is required.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile

from fontTools import version as fonttools_version
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import SVGPath
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

UNICODE = '18.0.0'
BASE_URL = 'https://kamichikoichi.github.io/jigmo/Jigmo-20250912.zip'
# Independently verify the release used for the first catalog survey.
BASE_SHA256 = '5744c7386d129475d87607ca66d043c8793c65448adeaedc921b6931890e5d0b'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def download(url, path):
    if path.exists():
        return path.read_bytes()
    for attempt in range(3):
        try:
            req = Request(url, headers={'User-Agent': 'Typdex-Jigmo-Unicode18/1.0'})
            with urlopen(req, timeout=45) as response:
                data = response.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return data
        except HTTPError as error:
            if error.code == 404:
                return None
            if attempt == 2:
                raise
        except OSError:
            if attempt == 2:
                raise
        time.sleep(1 + attempt)


def named_points(text):
    result = {}
    first = None
    for line in text.splitlines():
        fields = line.split(';')
        cp, name = int(fields[0], 16), fields[1]
        if name.endswith(', First>'):
            first = (cp, name)
        elif name.endswith(', Last>'):
            for point in range(first[0], cp + 1):
                result[point] = first[1]
            first = None
        else:
            result[cp] = name
    return result


def new_repertoire(ucd, ages):
    names = named_points(ucd)
    new = set()
    for line in ages.splitlines():
        clean = line.split('#', 1)[0].strip()
        if not clean:
            continue
        span, age = [s.strip() for s in clean.split(';')]
        if age != '18.0':
            continue
        ends = span.split('..')
        for cp in range(int(ends[0], 16), int(ends[-1], 16) + 1):
            name = names.get(cp, '').upper()
            if any(word in name for word in ('CJK', 'JURCHEN', 'SEAL', 'HIRAGANA',
                                             'KATAKANA', 'HENTAIGANA', 'BOPOMOFO',
                                             'IDEOGRAPHIC', 'TANGUT', 'KHITAN')):
                new.add(cp)
    return new


def svg_glyph(data, upm=1024):
    tree = ET.fromstring(data)
    if tree.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('Response is not SVG')
    if tree.attrib.get('viewBox') != '0 0 200 200':
        raise ValueError('Unexpected GlyphWiki viewBox')
    if not any(node.tag.endswith('path') and node.attrib.get('d', '').strip()
               for node in tree.iter()):
        return None
    pen = TTGlyphPen(None)
    # Same import scale (1024/200), 105% expansion about (512,307), and
    # +30 baseline shift as upstream makefont.pl. y starts at typo ascent 880.
    # This matches the published U+4E00 bounds to rounding precision.
    scale = upm / 1024
    transform = (5.376 * scale, 0, 0, -5.376 * scale, -25.6 * scale, 938.65 * scale)
    SVGPath.fromstring(data).draw(TransformPen(Cu2QuPen(pen, max_err=1), transform))
    glyph = pen.glyph()
    return glyph if glyph.numberOfContours > 0 else None


def get_svg(cp, work, offline=False):
    url = f'https://glyphwiki.org/glyph/u{cp:x}.svg'
    path = work / 'glyph' / f'u{cp:x}.svg'
    if offline and not path.exists():
        return cp, None, {'codepoint': cp, 'url': url, 'status': 'not-cached'}
    data = download(url, path)
    if data is None:
        return cp, None, {'codepoint': cp, 'url': url, 'status': 'not-found'}
    glyph = svg_glyph(data)
    return cp, data if glyph else None, {'codepoint': cp, 'url': url,
        'sha256': sha(data), 'bytes': len(data), 'status': 'available' if glyph else 'empty'}


def extend_font(data, additions, family):
    font = TTFont(BytesIO(data), recalcTimestamp=False)
    # glyf.__setitem__ appends to its own glyph-order list. Keep a separate
    # desired order so adding a glyph cannot append its name twice.
    order = list(font.getGlyphOrder())
    before = set(font.getBestCmap())
    if not any(t.isUnicode() and t.format == 12 for t in font['cmap'].tables):
        table = CmapSubtable.newSubtable(12)
        table.platformID, table.platEncID, table.language = 3, 10, 0
        table.cmap = dict(font.getBestCmap())
        font['cmap'].tables.append(table)
    vertical = font.get('vmtx')
    actual = []
    for cp, svg in sorted(additions.items()):
        if cp in before:
            continue
        name = f'u18_{cp:05X}'
        glyph = svg_glyph(svg, font['head'].unitsPerEm)
        if glyph is None:
            continue
        font['glyf'][name] = glyph
        glyph.recalcBounds(font['glyf'])
        order.append(name)
        font['hmtx'][name] = (font['head'].unitsPerEm, glyph.xMin)
        if vertical is not None:
            vertical[name] = (font['head'].unitsPerEm, font['OS/2'].sTypoAscender - glyph.yMax)
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format != 14:
                if table.format in (12, 13) or cp <= 0xFFFF:
                    table.cmap[cp] = name
        actual.append(cp)
    if len(order) > 65535:
        raise ValueError(f'{family} would exceed the OpenType glyph limit')
    font.setGlyphOrder(order)
    font['head'].fontRevision = 18.0
    names = {1: family, 2: 'Regular', 3: family.replace(' ', '') + '-Unicode18-20261020',
             4: family + ' Regular', 5: 'Version 18.000 experimental; Unicode 18 East Asian update',
             6: family.replace(' ', '') + '-Regular',
             13: 'Published Jigmo data: CC0 1.0 Universal. Added GlyphWiki data: '
                 'GlyphWiki data license (free use, reproduction and modification).',
             14: 'https://en.glyphwiki.org/wiki/GlyphWiki:License',
             16: family, 17: 'Regular'}
    for name_id, value in names.items():
        font['name'].removeNames(nameID=name_id)
        font['name'].setName(value, name_id, 3, 1, 0x409)
    font['name'].setName('Jigmo by Koichi Kamichi and GlyphWiki contributors; '
                         'Unicode 18 additions compiled by Typdex.', 0, 3, 1, 0x409)
    stream = BytesIO()
    font.save(stream)
    font.close()
    result = stream.getvalue()
    with TTFont(BytesIO(result), lazy=True) as check:
        after = set(check.getBestCmap())
        if not before <= after or not set(actual) <= after:
            raise ValueError('Built font lost baseline or added cmap mappings')
        glyph_count = check['maxp'].numGlyphs
    return result, {'family': family, 'baseline_mapped': len(before), 'mapped': len(after),
                    'added_codepoints': actual, 'glyph_count': glyph_count,
                    'sha256': sha(result), 'bytes': len(result)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('work/unicode18'))
    parser.add_argument('--output', type=Path, default=Path('build/unicode18'))
    parser.add_argument('--extra-codepoints', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--offline', action='store_true', help='rebuild only from cached input bytes')
    parser.add_argument('--manifest', type=Path, help='rebuild only the available outlines in a previous report; verify input hashes')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 8:
        parser.error('--jobs must be 1 through 8')
    args.work.mkdir(parents=True, exist_ok=True)
    if args.offline:
        for filename in ['Jigmo-20250912.zip', 'UnicodeData.txt', 'DerivedAge.txt']:
            if not (args.work / filename).exists():
                raise FileNotFoundError('Offline input missing: ' + filename)
    base = download(BASE_URL, args.work / 'Jigmo-20250912.zip')
    if sha(base) != BASE_SHA256:
        raise ValueError('Published Jigmo release hash mismatch')
    ucd = download(f'https://www.unicode.org/Public/{UNICODE}/ucd/UnicodeData.txt', args.work / 'UnicodeData.txt')
    age = download(f'https://www.unicode.org/Public/{UNICODE}/ucd/DerivedAge.txt', args.work / 'DerivedAge.txt')
    requested = new_repertoire(ucd.decode(), age.decode())
    if args.extra_codepoints:
        for line in args.extra_codepoints.read_text().splitlines():
            clean = line.split('#', 1)[0].strip()
            if clean:
                requested.add(int(clean.removeprefix('U+'), 16))
    locked = None
    if args.manifest:
        locked = json.loads(args.manifest.read_text())
        if (locked['unicode_version'] != UNICODE or locked['base_sha256'] != sha(base) or
                locked['unicode_data_sha256'] != sha(ucd) or locked['derived_age_sha256'] != sha(age)):
            raise ValueError('Locked manifest input mismatch')
        requested = {g['codepoint'] for g in locked['glyphs']}
    print(f'Requested {len(requested)} code points.', flush=True)
    svgs, provenance = {}, []
    expected = {g['codepoint']: g for g in locked['glyphs']} if locked else {}
    fetch_points = {cp for cp in requested if not locked or expected[cp]['status'] == 'available'}
    if locked:
        provenance = [g for cp, g in expected.items() if cp not in fetch_points]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(get_svg, cp, args.work, args.offline) for cp in sorted(fetch_points)]
        for index, future in enumerate(as_completed(futures), 1):
            cp, svg, record = future.result()
            if locked and (not svg or record['sha256'] != expected[cp]['sha256']):
                raise ValueError(f'Locked glyph input mismatch: U+{cp:04X}')
            if svg:
                svgs[cp] = svg
            provenance.append(record)
            if index % 100 == 0 or index == len(futures):
                print(f'SVGs checked: {index}/{len(futures)}; available: {len(svgs)}', flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'unicode_version': UNICODE, 'build_time': datetime.now(timezone.utc).isoformat(),
              'builder_sha256': sha(Path(__file__).read_bytes()),
              'fonttools_version': fonttools_version, 'base_url': BASE_URL, 'base_sha256': sha(base),
              'data_licenses': ['CC0-1.0 (published Jigmo)', 'LicenseRef-GlyphWiki-Data (new SVGs)'],
              'unicode_data_sha256': sha(ucd), 'derived_age_sha256': sha(age),
              'requested': len(requested), 'available': len(svgs),
              'unavailable': sorted(requested - svgs.keys()), 'fonts': [],
              'glyphs': sorted(provenance, key=lambda r: r['codepoint'])}
    (args.work / 'acquisition-report.json').write_text(json.dumps(report, indent=2) + '\n')
    with zipfile.ZipFile(BytesIO(base)) as archive:
        for filename, family, plane in [('Jigmo.ttf', 'Typdex Jigmo U18', 1),
                                        ('Jigmo2.ttf', 'Typdex Jigmo2 U18', 2),
                                        ('Jigmo3.ttf', 'Typdex Jigmo3 U18', 3)]:
            member = next(n for n in archive.namelist() if Path(n).name == filename)
            additions = {cp: svg for cp, svg in svgs.items()
                         if (cp < 0x20000 if plane == 1 else cp >> 16 == plane)}
            data, metadata = extend_font(archive.read(member), additions, family)
            dest = args.output / (family.replace(' ', '') + '-Regular.ttf')
            dest.write_bytes(data)
            metadata['file'] = dest.name
            report['fonts'].append(metadata)
            print(f'{dest.name}: {len(metadata["added_codepoints"])} added scalars; '
                  f'{metadata["glyph_count"]} glyphs', flush=True)
    (args.output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Build complete. Review build-report.json for unavailable glyphs and provenance.', flush=True)


if __name__ == '__main__':
    main()
