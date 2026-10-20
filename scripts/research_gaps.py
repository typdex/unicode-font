"""Explain which new fonts fill each gap in the fixed first-survey baseline."""
from collections import Counter
import csv
from io import StringIO
import json

from build_catalog import compact_ranges, expand, properties, file_count


def resolve(baseline_blocks, fonts, ages):
    """Group consecutive formerly missing scalars only when age and matches agree."""
    font_sets = {f['id']: expand(f['mapped_ranges']) for f in fonts}
    groups, contributions, unique = [], Counter(), Counter()
    by_block = []
    for block in baseline_blocks:
        points = expand(block['missing_ranges'])
        filled = 0
        for cp in sorted(points):
            hits = tuple(fid for fid, values in font_sets.items() if cp in values)
            version = ages[cp]
            for fid in hits:
                contributions[fid] += 1
            if len(hits) == 1:
                unique[hits[0]] += 1
            filled += bool(hits)
            key = (block['block'], version, hits)
            if groups and groups[-1]['_key'] == key and groups[-1]['end'] + 1 == cp:
                groups[-1]['end'] = cp
                groups[-1]['count'] += 1
            else:
                groups.append({'block': block['block'], 'start': cp, 'end': cp, 'count': 1,
                               'introduced_unicode_version': version,
                               'status': 'resolved' if hits else 'unresolved',
                               'font_ids': list(hits), '_key': key})
        by_block.append({'block': block['block'], 'previously_missing': len(points),
                         'resolved': filled, 'still_missing': len(points) - filled})
    for group in groups:
        del group['_key']
    return groups, contributions, unique, by_block


def research_outputs(root, sources, evidence, rows):
    baseline = json.loads((root / 'data/baseline/gaps.json').read_text())
    baseline_fonts = json.loads((root / 'data/baseline/font-coverage.json').read_text())['fonts']
    original = {f['id']: f for f in baseline_fonts}
    current = {f['id']: f for f in evidence['fonts']}
    if baseline['summary']['unicode_version'] != sources['unicode_version']:
        raise ValueError('Gap comparison requires the same Unicode baseline')
    # This research round adds candidates to a fixed survey. Refuse a hidden
    # replacement/removal, which could make its improvement claims misleading.
    for fid, font in original.items():
        if fid not in current or font['sha256'] != current[fid]['sha256']:
            raise ValueError('Baseline font changed: ' + fid)
        if font['mapped_ranges'] != current[fid]['mapped_ranges']:
            raise ValueError('Baseline font mappings changed: ' + fid)
    new_fonts = [f for f in evidence['fonts'] if f['id'] not in original]
    ages = {cp: version for a, b, version in properties((root / 'data/ucd/DerivedAge.txt').read_text())
            for cp in range(a, b + 1)}
    groups, counts, unique, blocks = resolve(baseline['blocks'], new_fonts, ages)
    total = sum(b['previously_missing'] for b in blocks)
    filled = sum(b['resolved'] for b in blocks)
    if total != baseline['summary']['missing_codepoints']:
        raise ValueError('Baseline gap counts do not reconcile')
    if total - filled != sum(r['missing_count'] for r in rows):
        raise ValueError('Gap research does not reconcile with current catalog')
    missing_points = {cp for b in baseline['blocks'] for cp in expand(b['missing_ranges'])}
    candidates = [{'font_id': f['id'], 'family': f['family'], 'project': f['project'],
                   'is_foss': f['license_info']['is_foss'],
                   'commercial_use': f['license_info']['commercial_use'],
                   'fills_baseline_gaps': counts[f['id']],
                   'unique_among_added_fonts': unique[f['id']],
                   'filled_ranges': compact_ranges(expand(f['mapped_ranges']) & missing_points)}
                  for f in new_fonts]
    candidates.sort(key=lambda f: (-f['fills_baseline_gaps'], f['font_id']))
    summary = {'unicode_version': sources['unicode_version'], 'baseline_font_files': len(original),
               'added_font_files': file_count(new_fonts), 'added_font_faces': len(new_fonts), 'previously_missing': total,
               'resolved': filled, 'still_missing': total - filled}
    result = {'summary': summary, 'candidates': candidates, 'blocks': blocks, 'ranges': groups}
    files = {'data/gap-research.json': json.dumps(result, indent=2) + '\n'}
    stream = StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['block', 'unicode_version', 'introduced_unicode_version', 'start', 'end',
                     'count', 'status', 'font_ids', 'font_families', 'foss_font_ids', 'non_foss_font_ids'])
    for g in groups:
        writer.writerow([g['block'], sources['unicode_version'], g['introduced_unicode_version'],
                         f"U+{g['start']:04X}", f"U+{g['end']:04X}", g['count'], g['status'],
                         '; '.join(g['font_ids']), '; '.join(current[f]['family'] for f in g['font_ids']),
                         '; '.join(f for f in g['font_ids'] if current[f]['license_info']['is_foss']),
                         '; '.join(f for f in g['font_ids'] if not current[f]['license_info']['is_foss'])])
    files['reports/gap-resolution.csv'] = stream.getvalue()
    inputs = {s['id']: s for s in sources['inputs']}
    lines = ['# Additional font research', '',
             f"Evaluation baseline: **Unicode {sources['unicode_version']}**. "
             f"The original {len(original)} files left **{total:,} targets** unmapped. "
             f"Adding {file_count(new_fonts)} files ({len(new_fonts)} faces) resolves **{filled:,}**; **{total - filled:,}** remain.", '',
             'Counts below intersect actual font cmaps with the fixed original missing-code-point set. '
             'Contributions overlap and must not be added. A zero result means the font adds alternatives '
             'but fills no gap from that baseline.', '',
             '| Added font | Unicode baseline | Non-FOSS | Commercial use | Previously missing targets mapped | Unique among added fonts |',
             '| --- | --- | --- | --- | ---: | ---: |']
    for f in candidates:
        if not f['fills_baseline_gaps']:
            continue
        source = inputs[current[f['font_id']]['source_id']]
        label = f['family'] + ' / ' + current[f['font_id']]['style']
        lines.append(f"| [{label}]({source['url']}) | {sources['unicode_version']} | "
                     f"{'No' if f['is_foss'] else 'Yes'} | {f['commercial_use']} | "
                     f"{f['fills_baseline_gaps']:,} | {f['unique_among_added_fonts']:,} |")
    zero = Counter(f['project'] for f in candidates if not f['fills_baseline_gaps'])
    lines += ['', 'Measured faces that fill no original gap: ' +
              '; '.join(f'{project}: {count}' for project, count in sorted(zero.items())) + '.', '']
    lines += ['', '## Results for each originally incomplete block', '',
              '| Block | Unicode baseline | Previously missing | Resolved | Still missing |',
              '| --- | --- | ---: | ---: | ---: |']
    for b in blocks:
        lines.append(f"| {b['block']} | {sources['unicode_version']} | {b['previously_missing']:,} | "
                     f"{b['resolved']:,} | {b['still_missing']:,} |")
    lines += ['', '## Locate a font for a specific character', '',
              '[gap-resolution.csv](gap-resolution.csv) gives exact ranges, the Unicode version in which '
              'each character was introduced, and every added font that maps the range. Adjacent code points '
              'are grouped only when their block, character age and font candidates all match. '
              'Font IDs join to [fonts.csv](fonts.csv) for download URLs, archive members, licenses and hashes.', '',
              '```sh', 'python3 scripts/query.py --codepoint U+20000 --limit 0',
              'python3 scripts/query.py --codepoint U+13460 --limit 0', '```', '',
              'Remaining gaps are in [gaps.md](gaps.md). Unmeasured or rejected leads and license caveats '
              'are recorded in [research-notes.md](../docs/research-notes.md). '
              'Measured cmap support does not establish outline or shaping quality.', '']
    files['reports/additional-fonts.md'] = '\n'.join(lines)
    apple = [f for f in new_fonts if f['project'] == 'apple-macos']
    if apple:
        apple_union = set().union(*(expand(f['mapped_ranges']) for f in apple))
        others = set().union(*(expand(f['mapped_ranges']) for f in evidence['fonts'] if f['project'] != 'apple-macos'))
        new_apple = apple_union & missing_points
        # All zero-gain faces still appear in the full evidence and font CSV.
        apple_lines = ['# Apple-distributed font survey', '',
            f"Measured **{len(apple)} faces in {file_count(apple)} installed files** from "
            '**macOS 27.0.1, build 26A434**. Evaluation baseline: **Unicode 18.0.0**.', '',
            f"Their union maps **{len(apple_union & missing_points):,} originally missing targets**. "
            f"Of these, **{len(new_apple - others):,}** are absent from all other fonts in the expanded survey.", '',
            'This is the installed snapshot on the research machine, not a claim that every Apple '
            'downloadable font or every Apple platform has been surveyed. '
            '[Apple’s published font inventory](https://support.apple.com/en-us/122869) and '
            '[developer font page](https://developer.apple.com/fonts/) are discovery references; '
            'embedded font versions and locked file hashes identify the measured bytes.', '',
            'The measured Apple Color Emoji is version **22.0d3e2** and Apple Symbols is '
            '**22.0d3e1**. Their font release numbers are not Unicode-version claims.', '',
            'All collection faces are measured. Apple-distributed fonts include third-party fonts and '
            'OFL fonts: the latter are classified per face using explicit embedded license grants. '
            'The remaining fonts retain their platform/vendor terms. '
            '[fonts.csv](fonts.csv) has the version, collection face, non-FOSS and commercial-use columns.', '',
            '**LastResort.otf is excluded**: its cmap maps Unicode positions to generic block symbols, '
            'which would falsely inflate character coverage. No Apple font binaries are redistributed.', '',
            '| Originally incomplete block | Unicode baseline | Original gaps mapped by Apple fonts |',
            '| --- | --- | ---: |']
        for block in baseline['blocks']:
            apple_lines.append(f"| {block['block']} | {sources['unicode_version']} | "
                               f"{len(apple_union & expand(block['missing_ranges'])):,} |")
        apple_lines += ['', 'To remeasure a compatible licensed macOS installation:', '',
                        '```sh', '.venv/bin/python scripts/refresh.py --rescan-local', '```', '',
                        'If the OS changed its font bytes, inspect the changes before accepting a new lock. '
                        'Ordinary refreshes reuse the committed local-font evidence, so the public catalog '
                        'can be rebuilt on Linux without the proprietary binaries.', '']
        apple_lines += ['## Separate Apple developer downloads', '',
            'Apple’s [current developer font page](https://developer.apple.com/fonts/) also offers '
            'SF Pro, SF Compact, SF Mono, New York and script extensions. Those downloadable packages '
            'were reviewed as discovery and license references, not measured as additional binaries. '
            'Their download license limits use to specified Apple-interface design purposes; '
            'do not substitute those terms for the terms of an installed platform font. '
            'The catalog’s commercial-use column therefore retains a platform/font-license condition '
            'rather than a blanket commercial-use grant.', '']
        files['reports/apple-fonts.md'] = '\n'.join(apple_lines)
    return files
