"""Research checks for the experimental Unicode 18 Jigmo update."""
from pathlib import Path
import sys
import unittest
from io import BytesIO
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments/jigmo'))
from build_unicode18 import new_repertoire, svg_glyph, extend_font


class JigmoBuildTests(unittest.TestCase):
    def test_unicode18_range_names_are_selected(self):
        ucd = ('18E00;<Jurchen Character, First>;Lo\n'
               '18E01;<Jurchen Character, Last>;Lo\n'
               '3D000;<Seal Character, First>;Lo\n'
               '3D001;<Seal Character, Last>;Lo\n'
               '0041;LATIN CAPITAL LETTER A;Lu\n')
        ages = '18E00..18E01; 18.0\n3D000..3D001; 18.0\n0041; 1.1\n'
        self.assertEqual(new_repertoire(ucd, ages), {0x18E00, 0x18E01, 0x3D000, 0x3D001})

    def test_empty_svg_is_not_counted_as_a_character(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><g/></svg>'
        self.assertIsNone(svg_glyph(svg))

    def test_scaling_matches_published_jigmo_reference(self):
        # GlyphWiki u4e00, CC0; published Jigmo bbox is (50, 385, 974, 460).
        svg = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
               b'<path d="M 186 99 L 186 103 L 14 103 L 14 99 L 164 99 L 174 89 Z"/></svg>')
        glyph = svg_glyph(svg)
        glyph.recalcBounds(None)
        self.assertEqual((glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax), (50, 385, 974, 460))

    def test_extended_font_compiles_and_preserves_existing_mapping(self):
        builder = FontBuilder(1024, isTTF=True)
        builder.setupGlyphOrder(['.notdef', 'A'])
        builder.setupCharacterMap({0x41: 'A'})
        builder.setupGlyf({name: TTGlyphPen(None).glyph() for name in ['.notdef', 'A']})
        builder.setupHorizontalMetrics({name: (512, 0) for name in ['.notdef', 'A']})
        builder.setupHorizontalHeader(ascent=880, descent=-144)
        builder.setupNameTable({'familyName': 'Fixture', 'styleName': 'Regular'})
        builder.setupOS2(sTypoAscender=880, sTypoDescender=-144)
        builder.setupPost()
        builder.setupMaxp()
        stream = BytesIO()
        builder.save(stream)
        svg = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
               b'<path d="M 20 20 L 180 20 L 180 180 L 20 180 Z"/></svg>')
        result, meta = extend_font(stream.getvalue(), {0x18E00: svg}, 'Fixture U18')
        with TTFont(BytesIO(result)) as font:
            self.assertEqual(set(font.getBestCmap()), {0x41, 0x18E00})
            self.assertEqual(font['maxp'].numGlyphs, 3)
            self.assertEqual(font.getBestCmap()[0x41], 'A')
        self.assertEqual(meta['added_codepoints'], [0x18E00])


if __name__ == '__main__':
    unittest.main()
