"""Tests for research-critical boundary, union and provenance behavior."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_catalog import build, compact_ranges, expand, status, unicode_categories, license_fields, file_count, write_outputs
from refresh import scan_font, scan, fetch
from research_gaps import resolve
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib import TTCollection, TTFont


def ucd_line(cp, name, category):
    return f'{cp:04X};{name};{category};0;L;;;;;N;;;;;\n'


class UnicodeTests(unittest.TestCase):
    def test_range_expansion_including_supplementary(self):
        text = (ucd_line(0x20000, '<CJK Ideograph Extension B, First>', 'Lo') +
                ucd_line(0x20002, '<CJK Ideograph Extension B, Last>', 'Lo'))
        self.assertEqual(unicode_categories(text), {0x20000: 'Lo', 0x20001: 'Lo', 0x20002: 'Lo'})

    def test_invalid_range_fails(self):
        with self.assertRaises(ValueError):
            unicode_categories(ucd_line(0x20002, '<CJK, Last>', 'Lo'))

    def test_compact_ranges_roundtrip(self):
        points = {0, 1, 3, 0x10000, 0x10001, 0x10FFFF}
        self.assertEqual(expand(compact_ranges(points)), points)
        self.assertEqual(compact_ranges([]), [])

    def test_status_zero_denominator(self):
        self.assertEqual(status(0, 0), 'not-applicable')
        self.assertEqual(status(0, 1), 'uncovered')
        self.assertEqual(status(1, 2), 'partial')
        self.assertEqual(status(2, 2), 'complete')


class FontScanTests(unittest.TestCase):
    def make_font(self):
        builder = FontBuilder(1000, isTTF=True)
        names = ['.notdef', 'A', 'B']
        builder.setupGlyphOrder(names)
        builder.setupCharacterMap({0x41: 'A', 0x42: '.notdef'})
        builder.setupGlyf({name: TTGlyphPen(None).glyph() for name in names})
        builder.setupHorizontalMetrics({name: (500, 0) for name in names})
        builder.setupHorizontalHeader(ascent=800, descent=-200)
        builder.setupNameTable({'familyName': 'Fixture', 'styleName': 'Regular'})
        builder.setupOS2()
        builder.setupPost()
        builder.setupMaxp()
        supplementary = CmapSubtable.newSubtable(12)
        supplementary.platformID, supplementary.platEncID, supplementary.language = 0, 4, 0
        supplementary.cmap = {0x1F600: 'B'}
        builder.font['cmap'].tables.append(supplementary)
        variation = CmapSubtable.newSubtable(14)
        variation.platformID, variation.platEncID, variation.language = 0, 5, 0
        variation.cmap = {}
        variation.uvsDict = {0xFE0F: [(0x43, 'A')]}
        builder.font['cmap'].tables.append(variation)
        stream = BytesIO()
        builder.save(stream)
        return stream.getvalue()

    def test_cmap_union_nonzero_glyphs_and_supplementary(self):
        result = scan_font(self.make_font(), {'id': 'fixture', 'project': 'test'})
        self.assertEqual(expand(result['mapped_ranges']), {0x41, 0x1F600})
        self.assertEqual(result['mapped_count'], 2)

    def test_collection_faces_keep_ids_and_container_hash(self):
        collection = TTCollection()
        collection.fonts = [TTFont(BytesIO(self.make_font())), TTFont(BytesIO(self.make_font()))]
        buffer = BytesIO()
        collection.save(buffer)
        source = {'id': 'collection', 'project': 'test', 'kind': 'font'}
        faces = scan(source, buffer.getvalue())
        self.assertEqual([f['id'] for f in faces], ['collection::face-0', 'collection::face-1'])
        self.assertEqual(file_count(faces), 1)
        self.assertEqual(faces[0]['sha256'], faces[1]['sha256'])


class LocalFontTests(unittest.TestCase):
    def test_report_check_preserves_multiline_license_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'reports/fonts.csv': 'font,license\nExample,"line one\r\nline two"\n'}
            self.assertEqual(write_outputs(files, root=root), [])
            self.assertEqual(write_outputs(files, check=True, root=root), [])
            (root / 'reports/fonts.csv').write_bytes(files['reports/fonts.csv'].replace('\r\n', '\n').encode())
            self.assertEqual(write_outputs(files, check=True, root=root), ['reports/fonts.csv'])

    def test_locked_local_evidence_can_be_reused_without_binary(self):
        source = {'id': 'local', 'kind': 'local-font', 'path': '/not/installed.ttf', 'url': 'https://example.org'}
        lock = {'local': {'id': 'local', 'url': source['url'], 'sha256': 'known', 'bytes': 123}}
        _, data, entry = fetch(source, lock, False)
        self.assertIsNone(data)
        self.assertEqual(entry, lock['local'])
        with self.assertRaisesRegex(ValueError, '--rescan-local'):
            fetch(source, {}, True)

    def test_apple_ofl_face_overrides_platform_default(self):
        project = {'id': 'apple-macos', 'is_foss': False, 'license': 'proprietary',
                   'license_url': 'https://example.org/platform', 'commercial_use': 'platform-terms'}
        terms = license_fields({'embedded_license': 'Licensed under the SIL Open Font License, Version 1.1'}, project)
        self.assertTrue(terms['is_foss'])
        self.assertEqual(terms['license'], 'OFL-1.1')
        self.assertFalse(license_fields({}, project)['is_foss'])


class SurveyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ['catalog', 'data/ucd']:
            (self.root / directory).mkdir(parents=True)
        # Four blocks exercise complete by union, partial, uncovered and N/A.
        ucd = {'Blocks.txt': '0040..004F; Pair\n0050..005F; Partial\n0060..006F; Absent\nFE00..FE0F; Selectors\n',
               'UnicodeData.txt': ''.join([
                   ucd_line(0x40, 'CONTROL', 'Cc'),
                   ucd_line(0x41, 'LETTER A', 'Lu'), ucd_line(0x42, 'LETTER B', 'Lu'),
                   ucd_line(0x43, 'PRIVATE USE', 'Co'),
                   ucd_line(0x50, 'LETTER P', 'Lu'), ucd_line(0x51, 'LETTER Q', 'Lu'),
                   ucd_line(0x61, 'LETTER a', 'Ll'), ucd_line(0xFE00, 'VARIATION SELECTOR-1', 'Mn')]),
               'DerivedCoreProperties.txt': 'FE00..FE0F; Default_Ignorable_Code_Point\n',
               'DerivedAge.txt': '0040..004F; 1.1\n0050; 2.0\n0051; 18.0\n0061; 1.1\nFE00; 3.2\n'}
        sources = {'unicode_version': 'test', 'survey_date': '2026-10-20',
                   'projects': [{'id': 'one', 'license': 'test', 'is_foss': True},
                                {'id': 'two', 'license': 'test', 'is_foss': False}], 'inputs': []}
        lock = {'inputs': []}
        for filename, content in ucd.items():
            (self.root / 'data/ucd' / filename).write_text(content)
            entry = {'id': filename, 'url': 'https://example.org/' + filename}
            sources['inputs'].append(dict(entry, kind='ucd', filename=filename))
            lock['inputs'].append(dict(entry, sha256=hashlib.sha256(content.encode()).hexdigest()))
        fonts = []
        for fid, project, points in [('a', 'one', {0x41, 0x50}), ('b', 'two', {0x42, 0x50})]:
            sources['inputs'].append({'id': fid, 'url': 'https://example.org/' + fid, 'kind': 'font'})
            lock['inputs'].append({'id': fid, 'url': 'https://example.org/' + fid, 'sha256': fid})
            fonts.append({'id': fid, 'source_id': fid, 'project': project, 'family': fid,
                          'member': None, 'sha256': fid, 'mapped_ranges': compact_ranges(points),
                          'style': 'Regular', 'version': '1', 'mapped_count': len(points)})
        self.write_json('catalog/sources.json', sources)
        self.write_json('data/inputs.lock.json', lock)
        self.write_json('data/font-coverage.json', {'unicode_version': 'test', 'fonts': fonts})

    def write_json(self, path, value):
        (self.root / path).write_text(json.dumps(value))

    def test_union_and_denominator(self):
        _, _, _, rows = build(self.root)
        complete, partial, absent, selectors = rows
        self.assertEqual([r['status'] for r in rows], ['complete', 'partial', 'uncovered', 'not-applicable'])
        self.assertEqual(complete['target_count'], 2)  # no unassigned slots, Cc or Co
        self.assertTrue(all(f['status'] == 'partial' for f in complete['fonts']))
        self.assertEqual(complete['projects']['one']['covered'], 1)
        self.assertEqual(partial['missing_ranges'], [[0x51, 0x51]])
        self.assertEqual(partial['covered_count'], 1)  # same scalar in two fonts is counted once
        self.assertEqual(complete['foss_covered_count'], 1)
        self.assertEqual(complete['non_foss_covered_count'], 1)
        self.assertEqual(complete['foss_status'], 'partial')
        self.assertEqual(len(partial['fonts']), 2)
        self.assertEqual(absent['missing_ranges'], [[0x61, 0x61]])
        self.assertEqual(selectors['target_count'], 0)
        self.assertEqual(partial['first_character_unicode_version'], '2.0')
        self.assertEqual(partial['last_character_unicode_version'], '18.0')
        self.assertEqual(partial['missing_by_unicode_version'], {'18.0': 1})

    def test_modified_ucd_fails(self):
        (self.root / 'data/ucd/Blocks.txt').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            build(self.root)

    def test_missing_font_fails_instead_of_reporting_gap(self):
        evidence = json.loads((self.root / 'data/font-coverage.json').read_text())
        evidence['fonts'].pop()
        self.write_json('data/font-coverage.json', evidence)
        with self.assertRaisesRegex(ValueError, 'inventory'):
            build(self.root)

    def test_duplicate_source_ids_fail(self):
        sources = json.loads((self.root / 'catalog/sources.json').read_text())
        sources['inputs'].append(sources['inputs'][-1])
        self.write_json('catalog/sources.json', sources)
        with self.assertRaisesRegex(ValueError, 'Duplicate source'):
            build(self.root)

    def test_changed_font_hash_fails(self):
        evidence = json.loads((self.root / 'data/font-coverage.json').read_text())
        evidence['fonts'][0]['sha256'] = 'changed'
        self.write_json('data/font-coverage.json', evidence)
        with self.assertRaisesRegex(ValueError, 'Font hash mismatch'):
            build(self.root)


class GapResearchTests(unittest.TestCase):
    def test_ranges_split_on_age_candidates_and_holes(self):
        baseline = [{'block': 'test', 'missing_ranges': [[10, 15], [17, 17]]}]
        fonts = [{'id': 'a', 'mapped_ranges': [[10, 14], [17, 17]]},
                 {'id': 'b', 'mapped_ranges': [[12, 12]]}]
        ages = {cp: '17.0' if cp == 11 else '18.0' for cp in range(10, 18)}
        groups, counts, unique, blocks = resolve(baseline, fonts, ages)
        self.assertEqual([(g['start'], g['end']) for g in groups],
                         [(10, 10), (11, 11), (12, 12), (13, 14), (15, 15), (17, 17)])
        self.assertEqual(groups[2]['font_ids'], ['a', 'b'])
        self.assertEqual(groups[4]['status'], 'unresolved')
        self.assertEqual(counts, {'a': 6, 'b': 1})
        self.assertEqual(unique['a'], 5)
        self.assertEqual(unique['b'], 0)
        self.assertEqual(blocks[0]['resolved'], 6)  # overlapping hits counted once
        self.assertEqual(blocks[0]['still_missing'], 1)


if __name__ == '__main__':
    unittest.main()
