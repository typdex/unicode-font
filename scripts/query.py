#!/usr/bin/env python3
"""Search the committed catalog without network access or extra dependencies."""
import argparse
import json
from pathlib import Path
from build_catalog import range_text, properties, license_fields

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--block', help='case-insensitive block name substring')
    group.add_argument('--codepoint', help='hexadecimal scalar, e.g. U+1E900')
    parser.add_argument('--limit', type=int, default=10, help='maximum fonts per block; 0 means all')
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    catalog = json.loads((ROOT / 'data/blocks.json').read_text())
    evidence = json.loads((ROOT / 'data/font-coverage.json').read_text())
    sources = json.loads((ROOT / 'catalog/sources.json').read_text())
    inputs = {s['id']: s for s in sources['inputs']}
    projects = {p['id']: p for p in sources['projects']}
    cp = None
    if args.codepoint:
        try:
            cp = int(args.codepoint.upper().removeprefix('U+'), 16)
        except ValueError:
            parser.error('codepoint must be hexadecimal')
        if not 0 <= cp <= 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
            parser.error('codepoint must be a Unicode scalar value')
    rows = [r for r in catalog['blocks']
            if (r['start'] <= cp <= r['end'] if cp is not None
                else args.block.casefold() in r['block'].casefold())]
    if not rows:
        raise SystemExit('No matching block (the scalar may be outside any named block).')
    font_map = {f['id']: f for f in evidence['fonts']}
    for row in rows:
        print(f"{row['block']} (U+{row['start']:04X}–U+{row['end']:04X}): {row['status']}")
        print(f"  {row['covered_count']}/{row['target_count']} targets mapped; {row['missing_count']} missing")
        if cp is None:
            hits = [font_map[h['font_id']] for h in row['fonts']]
            missing = range_text(row['missing_ranges'])
            if missing:
                print('  Missing: ' + missing)
        else:
            hits = [f for f in evidence['fonts'] if any(a <= cp <= b for a, b in f['mapped_ranges'])]
            age = next((v for a, b, v in properties((ROOT / 'data/ucd/DerivedAge.txt').read_text())
                        if a <= cp <= b), 'unassigned in this baseline')
            print(f'  Unicode introduced: {age}; evaluation baseline: {catalog["summary"]["unicode_version"]}')
            research_path = ROOT / 'data/gap-research.json'
            if research_path.exists():
                research = json.loads(research_path.read_text())
                group = next((g for g in research['ranges'] if g['start'] <= cp <= g['end']), None)
                if group:
                    print('  Original survey gap: ' + group['status'])
            print(f'  U+{cp:04X}: {len(hits)} scalar cmap matches (may be outside the target metric)')
        for font in hits[:args.limit or None]:
            member = ' :: ' + font['member'] if font['member'] else ''
            terms = license_fields(font, projects[font['project']])
            print(f"  {font['family']} / {font['style']} [{font['project']}; "
                  f"{'FOSS' if terms['is_foss'] else 'non-FOSS'}] — {font['id']}")
            print('    Commercial use: ' + str(terms['commercial_use']))
            print('    ' + inputs[font['source_id']]['url'] + member)
            if inputs[font['source_id']]['kind'] == 'local-font':
                print('    Local input: ' + inputs[font['source_id']]['path'])
        if args.limit and len(hits) > args.limit:
            print(f'  … {len(hits) - args.limit} more; use --limit 0')


if __name__ == '__main__':
    main()
