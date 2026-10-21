#!/usr/bin/env python3
"""Build deterministic, offline Unicode block reports from committed evidence."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compact_ranges(points):
    result = []
    for cp in sorted(points):
        if result and cp == result[-1][1] + 1:
            result[-1][1] = cp
        else:
            result.append([cp, cp])
    return result


def expand(ranges):
    return {cp for start, end in ranges for cp in range(start, end + 1)}


def properties(text, wanted=None):
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        span, prop = [s.strip() for s in line.split(';')[:2]]
        limits = span.split('..')
        if wanted is None or prop == wanted:
            yield int(limits[0], 16), int(limits[-1], 16), prop


def unicode_categories(text):
    """Handle UCD First/Last records (CJK, Hangul, surrogates, PUA)."""
    result = {}
    first = None
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split(';')
        cp, name, category = int(fields[0], 16), fields[1], fields[2]
        if name.endswith(', First>'):
            first = (cp, category)
        elif name.endswith(', Last>'):
            if first is None or first[1] != category:
                raise ValueError('Mismatched UnicodeData range')
            result.update((point, category) for point in range(first[0], cp + 1))
            first = None
        else:
            result[cp] = category
    if first is not None:
        raise ValueError('Unclosed UnicodeData range')
    return result


def range_text(ranges):
    return ', '.join(f'U+{a:04X}' if a == b else f'U+{a:04X}–U+{b:04X}' for a, b in ranges)


def status(covered, target):
    if target == 0:
        return 'not-applicable'
    return 'complete' if covered == target else 'partial' if covered else 'uncovered'


def license_fields(font, project):
    result = {key: project.get(key) for key in ('is_foss', 'license', 'license_url',
              'commercial_use', 'commercial_redistribution', 'modification')}
    # Apple distributes some OFL fonts alongside proprietary platform fonts.
    # Classify those faces using their own explicit embedded license grant.
    declaration = (font.get('embedded_license') or '').lower()
    if project['id'] == 'apple-macos' and 'open font license' in declaration:
        result.update(is_foss=True, license='OFL-1.1',
                      license_url=font.get('embedded_license_url') or project['license_url'],
                      commercial_use='permitted-with-license-conditions',
                      commercial_redistribution='permitted-with-license-conditions',
                      modification='permitted-with-license-conditions')
    return result


def file_count(fonts):
    return len({(f['source_id'], f['member']) for f in fonts})


def build(root=ROOT):
    sources = json.loads((root / 'catalog/sources.json').read_text())
    lock = json.loads((root / 'data/inputs.lock.json').read_text())
    for label, entries in [('source', sources['inputs']), ('lock', lock['inputs']),
                           ('project', sources['projects'])]:
        if len({e['id'] for e in entries}) != len(entries):
            raise ValueError('Duplicate ' + label + ' IDs')
    locked = {s['id']: s for s in lock['inputs']}
    for source in sources['inputs']:
        entry = locked.get(source['id'])
        if not entry or entry['url'] != source['url']:
            raise ValueError('Missing or stale lock: ' + source['id'])
        if source['kind'] == 'ucd':
            data = (root / 'data/ucd' / source['filename']).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('UCD hash mismatch: ' + source['id'])
    ucd = root / 'data/ucd'
    categories = unicode_categories((ucd / 'UnicodeData.txt').read_text())
    ages = {cp: version for a, b, version in properties((ucd / 'DerivedAge.txt').read_text())
            for cp in range(a, b + 1)}
    ignorable = expand([(a, b) for a, b, _ in properties(
        (ucd / 'DerivedCoreProperties.txt').read_text(), 'Default_Ignorable_Code_Point')])
    # Glyph-oriented denominator. Excludes unassigned, controls, formats, PUA,
    # surrogates, line/paragraph separators, and default-ignorable characters.
    targets = {cp for cp, cat in categories.items()
               if (cat[0] in 'LMNPS' or cat == 'Zs') and cp not in ignorable}
    evidence = json.loads((root / 'data/font-coverage.json').read_text())
    if len({f['id'] for f in evidence['fonts']}) != len(evidence['fonts']):
        raise ValueError('Duplicate font IDs')
    if evidence['unicode_version'] != sources['unicode_version']:
        raise ValueError('Unicode version mismatch')
    projects_meta = {p['id']: p for p in sources['projects']}
    for font in evidence['fonts']:
        font['license_info'] = license_fields(font, projects_meta[font['project']])
    font_sets = {f['id']: expand(f['mapped_ranges']) for f in evidence['fonts']}
    expected_fonts = {s['id'] for s in sources['inputs'] if s['kind'] in ('font', 'local-font', 'zip', 'tar')}
    if {f['source_id'] for f in evidence['fonts']} != expected_fonts:
        raise ValueError('Font evidence does not match source inventory')
    for f in evidence['fonts']:
        if f['member'] is None and f['sha256'] != locked[f['source_id']]['sha256']:
            raise ValueError('Font hash mismatch: ' + f['id'])
    font_meta = {f['id']: f for f in evidence['fonts']}
    rows = []
    for start, end, name in properties((ucd / 'Blocks.txt').read_text()):
        target = targets.intersection(range(start, end + 1))
        versions = sorted({ages[cp] for cp in categories.keys() & set(range(start, end + 1))},
                          key=lambda value: tuple(map(int, value.split('.'))))
        assigned = sum(cp in categories for cp in range(start, end + 1))
        hits, union, projects, foss, non_foss = [], set(), {}, set(), set()
        for fid, points in font_sets.items():
            overlap = target & points
            if overlap:
                union |= overlap
                project = font_meta[fid]['project']
                projects.setdefault(project, set()).update(overlap)
                (foss if font_meta[fid]['license_info']['is_foss'] else non_foss).update(overlap)
                hits.append({'font_id': fid, 'family': font_meta[fid]['family'],
                             'covered': len(overlap), 'status': status(len(overlap), len(target)),
                             'is_foss': font_meta[fid]['license_info']['is_foss'],
                             'commercial_use': font_meta[fid]['license_info']['commercial_use']})
        hits.sort(key=lambda h: (-h['covered'], h['font_id']))
        rows.append({'block': name, 'start': start, 'end': end,
                     'unicode_version': sources['unicode_version'],
                     'first_character_unicode_version': versions[0] if versions else None,
                     'last_character_unicode_version': versions[-1] if versions else None,
                     'character_unicode_versions': versions,
                     'assigned_count': assigned, 'target_count': len(target),
                     'excluded_assigned_count': assigned - len(target),
                     'covered_count': len(union), 'missing_count': len(target - union),
                     'foss_covered_count': len(foss), 'non_foss_covered_count': len(non_foss),
                     'foss_status': status(len(foss), len(target)),
                     'status': status(len(union), len(target)),
                     'missing_ranges': compact_ranges(target - union),
                     'missing_by_unicode_version': dict(sorted(Counter(ages[cp] for cp in target - union).items(),
                         key=lambda item: tuple(map(int, item[0].split('.'))))),
                     'projects': {p: {'covered': len(points), 'status': status(len(points), len(target))}
                                  for p, points in sorted(projects.items())},
                     'fonts': hits})
    return sources, lock, evidence, rows


def outputs(sources, lock, evidence, rows):
    counts = dict(sorted(Counter(r['status'] for r in rows).items()))
    summary = {'unicode_version': sources['unicode_version'], 'survey_date': sources['survey_date'],
               'blocks': len(rows), 'font_files': file_count(evidence['fonts']),
               'font_faces': len(evidence['fonts']),
               'projects': len(sources['projects']), 'block_status': counts,
               'target_codepoints': sum(r['target_count'] for r in rows),
               'covered_codepoints': sum(r['covered_count'] for r in rows),
               'missing_codepoints': sum(r['missing_count'] for r in rows)}
    summary['foss_covered_codepoints'] = sum(r['foss_covered_count'] for r in rows)
    summary['non_foss_covered_codepoints'] = sum(r['non_foss_covered_count'] for r in rows)
    summary['non_foss_only_codepoints'] = summary['covered_codepoints'] - summary['foss_covered_codepoints']
    summary['missing_foss_codepoints'] = summary['target_codepoints'] - summary['foss_covered_codepoints']
    summary['foss_block_status'] = dict(sorted(Counter(r['foss_status'] for r in rows).items()))
    summary['project_summary'] = {}
    for p in sources['projects']:
        project_counts = Counter(status(r['projects'].get(p['id'], {}).get('covered', 0), r['target_count'])
                                 for r in rows)
        summary['project_summary'][p['id']] = {
            'font_files': file_count([f for f in evidence['fonts'] if f['project'] == p['id']]),
            'font_faces': sum(f['project'] == p['id'] for f in evidence['fonts']),
            'covered_codepoints': sum(r['projects'].get(p['id'], {}).get('covered', 0) for r in rows),
            'block_status': dict(sorted(project_counts.items()))}
    files = {'data/blocks.json': json.dumps({'summary': summary, 'blocks': rows}, indent=2) + '\n'}
    from io import StringIO
    csv_out = StringIO(newline='')
    writer = csv.writer(csv_out, lineterminator='\n')
    writer.writerow(['block', 'first_character_unicode_version',
                     'last_character_unicode_version', 'start', 'end', 'status', 'assigned', 'targets', 'covered', 'missing',
                     'foss_covered', 'non_foss_covered', 'foss_status',
                     'projects', 'missing_ranges'])
    for r in rows:
        writer.writerow([r['block'], r['first_character_unicode_version'],
                         r['last_character_unicode_version'], f"U+{r['start']:04X}", f"U+{r['end']:04X}", r['status'],
                         r['assigned_count'], r['target_count'], r['covered_count'], r['missing_count'],
                         r['foss_covered_count'], r['non_foss_covered_count'], r['foss_status'],
                         '; '.join(r['projects']), range_text(r['missing_ranges'])])
    files['reports/blocks.csv'] = csv_out.getvalue()
    project_out = StringIO(newline='')
    writer = csv.writer(project_out, lineterminator='\n')
    project_ids = [p['id'] for p in sources['projects']]
    writer.writerow(['block', 'unicode_version', 'targets'] + [p + '_covered' for p in project_ids])
    for r in rows:
        writer.writerow([r['block'], r['unicode_version'], r['target_count']] +
                        [r['projects'].get(p, {}).get('covered', 0) for p in project_ids])
    files['reports/projects.csv'] = project_out.getvalue()
    font_out = StringIO(newline='')
    writer = csv.writer(font_out, lineterminator='\n')
    writer.writerow(['font_id', 'family', 'style', 'project', 'version', 'unicode_version', 'sha256',
                     'mapped_scalars', 'is_foss', 'non_foss', 'commercial_use', 'commercial_redistribution',
                     'modification', 'license', 'license_evidence_url', 'embedded_license',
                     'embedded_license_url', 'url', 'archive_member', 'collection_face'])
    project_map = {p['id']: p for p in sources['projects']}
    input_map = {s['id']: s for s in sources['inputs']}
    for f in evidence['fonts']:
        terms = f['license_info']
        writer.writerow([f['id'], f['family'], f['style'], f['project'], f['version'], sources['unicode_version'],
                         f['sha256'], f['mapped_count'], terms['is_foss'], not terms['is_foss'],
                         terms['commercial_use'], terms['commercial_redistribution'], terms['modification'],
                         terms['license'], terms['license_url'], f.get('embedded_license'),
                         f.get('embedded_license_url'),
                         input_map[f['source_id']]['url'], f['member'] or '',
                         f.get('face_index') if f.get('face_index') is not None else ''])
    files['reports/fonts.csv'] = font_out.getvalue()
    lines = ['# Unicode block catalog', '',
             f"Unicode **{sources['unicode_version']}** · survey **{sources['survey_date']}** · "
             f"**{len(evidence['fonts'])} font faces in {file_count(evidence['fonts'])} files** "
             f"in **{len(sources['projects'])} projects**.", '',
             f"{len(rows)} blocks: " + '; '.join(f'{n} {s}' for s, n in counts.items()) + '.', '',
             'Coverage is the union of surveyed Unicode cmaps against assigned letters, marks, numbers, '
             'punctuation, symbols and space separators, excluding default-ignorables. '
             'It does not establish shaping or glyph correctness. See [methodology](../docs/methodology.md).', '',
             'Font names below link to the pinned artifact (or its upstream archive). '
             'The top five distinct families are shown; [blocks.json](../data/blocks.json) lists every matching font. '
             'A complete union may require multiple fonts.', '',
             'The Unicode evaluation baseline is given above. “Character versions” shows the earliest and latest '
             'character ages within a block, not a claim that a font implements an entire Unicode release.', '',
             'FOSS and non-FOSS counts are separate unions and can overlap. '
             'See [font license and commercial-use columns](fonts.csv) and [project license notes](licenses.md).', '',
             '| Block | Character versions | Range | Status | Mapped / target | FOSS mapped | Non-FOSS mapped | Font candidates (mapped count) |',
             '| --- | --- | --- | --- | ---: | ---: | ---: | --- |']
    source_map = {s['id']: s for s in sources['inputs']}
    font_map = {f['id']: f for f in evidence['fonts']}
    for r in rows:
        candidates, seen = [], set()
        for hit in r['fonts']:
            family = hit['family']
            if family in seen:
                continue
            seen.add(family)
            url = source_map[font_map[hit['font_id']]['source_id']]['url']
            candidates.append(f"[{family}]({url}) ({hit['covered']})")
            if len(candidates) == 5:
                break
        versions = r['first_character_unicode_version'] + '–' + r['last_character_unicode_version']
        lines.append(f"| {r['block']} | {versions} | U+{r['start']:04X}–U+{r['end']:04X} | {r['status']} | "
                     f"{r['covered_count']} / {r['target_count']} | {r['foss_covered_count']} | "
                     f"{r['non_foss_covered_count']} | " + ('; '.join(candidates) or '—') + ' |')
    files['reports/blocks.md'] = '\n'.join(lines) + '\n'
    gaps = ['# Coverage gaps', '',
            'These are gaps in this pinned survey, not evidence that no FOSS font exists. '
            'Counts use the glyph-oriented denominator in [methodology](../docs/methodology.md).', '',
            f"**{summary['missing_codepoints']:,} target code points** are absent from all surveyed font cmaps.", '',
            '## Entirely uncovered blocks', '',
            '| Block | Unicode | Missing character versions | Range | Missing targets |', '| --- | --- | --- | --- | ---: |']
    for r in rows:
        if r['status'] == 'uncovered':
            gaps.append(f"| {r['block']} | {r['unicode_version']} | {', '.join(r['missing_by_unicode_version'])} | U+{r['start']:04X}–U+{r['end']:04X} | {r['missing_count']} |")
    gaps += ['', '## Partially covered blocks', '',
             'Exact missing ranges are in [blocks.csv](blocks.csv) and [blocks.json](../data/blocks.json).', '',
             '| Block | Unicode | Missing character versions | Mapped / target | Missing |', '| --- | --- | --- | ---: | ---: |']
    for r in sorted(rows, key=lambda r: (-r['missing_count'], r['start'])):
        if r['status'] == 'partial':
            gaps.append(f"| {r['block']} | {r['unicode_version']} | {', '.join(r['missing_by_unicode_version'])} | {r['covered_count']} / {r['target_count']} | {r['missing_count']} |")
    gaps += ['', '## Blocks outside this metric', '',
             'Surrogates, private-use areas and default-ignorable-only blocks have no target glyphs. '
             'They are not counted as missing font support.', '']
    gaps.extend('- ' + r['block'] for r in rows if r['status'] == 'not-applicable')
    files['reports/gaps.md'] = '\n'.join(gaps) + '\n'
    files['reports/summary.json'] = json.dumps(summary, indent=2) + '\n'
    licenses = ['# Font licenses and commercial use', '',
                'Each font face has explicit `non_foss`, `commercial_use`, `commercial_redistribution` '
                'and `modification` columns in [fonts.csv](fonts.csv). Using a font in a commercial '
                'document and selling or redistributing the font binary are separate permissions.', '',
                '| Distribution | FOSS | Commercial use | Commercial font redistribution | Modification | Evidence |',
                '| --- | --- | --- | --- | --- | --- |']
    for p in sources['projects']:
        classification = 'Mixed; per-face embedded OFL checked' if p['id'] == 'apple-macos' else ('Yes' if p['is_foss'] else 'No')
        licenses.append(f"| {p['name']} | {classification} | {p['commercial_use']} | "
                        f"{p['commercial_redistribution']} | {p['modification']} | [{p['license']}]({p['license_url']}) |")
    files['reports/licenses.md'] = '\n'.join(licenses) + '\n'
    if (ROOT / 'data/baseline/gaps.json').exists():
        from research_gaps import research_outputs
        files.update(research_outputs(ROOT, sources, evidence, rows))
    return files


def write_outputs(files, check=False, root=ROOT):
    stale = []
    for name, content in files.items():
        path = root / name
        data = content.encode('utf-8')
        if check:
            # Embedded font-license fields may contain CRLF inside CSV cells.
            # Compare exact bytes, without universal-newline translation.
            if not path.exists() or path.read_bytes() != data:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return stale


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if generated reports differ')
    args = parser.parse_args()
    stale = write_outputs(outputs(*build()), args.check)
    if stale:
        raise SystemExit('Stale outputs: ' + ', '.join(stale))
    print('Reports verified.' if args.check else 'Reports generated.')


if __name__ == '__main__':
    main()
