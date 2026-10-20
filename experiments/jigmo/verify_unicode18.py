#!/usr/bin/env python3
"""Verify that an experimental Jigmo update preserves the published fonts."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile

from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-zip', type=Path, required=True)
    parser.add_argument('--fonts', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    if hashlib.sha256(args.base_zip.read_bytes()).hexdigest() != report['base_sha256']:
        raise ValueError('Base archive hash mismatch')
    checks = []
    with zipfile.ZipFile(args.base_zip) as archive:
        for oldname, expected in zip(['Jigmo.ttf', 'Jigmo2.ttf', 'Jigmo3.ttf'], report['fonts']):
            member = next(n for n in archive.namelist() if Path(n).name == oldname)
            data = (args.fonts / expected['file']).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected['sha256']:
                raise ValueError('Built font hash mismatch: ' + expected['file'])
            with TTFont(BytesIO(archive.read(member)), lazy=True) as before, TTFont(BytesIO(data), lazy=True) as after:
                oldmap, newmap = before.getBestCmap(), after.getBestCmap()
                if not all(newmap.get(cp) == name for cp, name in oldmap.items()):
                    raise ValueError('Baseline scalar mapping changed')
                order = before.getGlyphOrder()
                if after.getGlyphOrder()[:len(order)] != order:
                    raise ValueError('Baseline glyph order changed')
                old14 = [t.uvsDict for t in before['cmap'].tables if t.format == 14]
                new14 = [t.uvsDict for t in after['cmap'].tables if t.format == 14]
                if old14 != new14:
                    raise ValueError('Variation sequences changed')
                for name in order:
                    if before['glyf'][name].compile(before['glyf']) != after['glyf'][name].compile(after['glyf']):
                        raise ValueError('Baseline outline or instructions changed: ' + name)
                unchanged_gsub = 'GSUB' not in before or before.getTableData('GSUB') == after.getTableData('GSUB')
                if not unchanged_gsub:
                    raise ValueError('Baseline GSUB changed')
                checks.append({'font': expected['file'], 'baseline_glyphs_unchanged': len(order),
                    'baseline_scalars_preserved': len(oldmap), 'glyph_order_prefix_preserved': True,
                    'variation_sequences_preserved': sum(len(v) for table in old14 for v in table.values()),
                    'gsub_preserved': unchanged_gsub, 'sha256_verified': True})
                print(expected['file'] + ': verified')
    args.output.write_text(json.dumps({'checks': checks}, indent=2) + '\n')


if __name__ == '__main__':
    main()
