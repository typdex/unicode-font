# Coverage gaps

These are gaps in this pinned survey, not evidence that no FOSS font exists. Counts use the glyph-oriented denominator in [methodology](../docs/methodology.md).

**2,343 target code points** are absent from all surveyed font cmaps.

## Entirely uncovered blocks

| Block | Unicode | Missing character versions | Range | Missing targets |
| --- | --- | --- | --- | ---: |
| Archaic Cuneiform Numerals | 18.0.0 | 18.0 | U+12550–U+1268F | 311 |
| Jurchen Radicals | 18.0.0 | 18.0 | U+191A0–U+191DF | 51 |

## Partially covered blocks

Exact missing ranges are in [blocks.csv](blocks.csv) and [blocks.json](../data/blocks.json).

| Block | Unicode | Missing character versions | Mapped / target | Missing |
| --- | --- | --- | ---: | ---: |
| Egyptian Hieroglyphs Extended-A | 18.0.0 | 16.0 | 2924 / 3995 | 1071 |
| Jurchen | 18.0.0 | 18.0 | 4 / 914 | 910 |

## Blocks outside this metric

Surrogates, private-use areas and default-ignorable-only blocks have no target glyphs. They are not counted as missing font support.

- High Surrogates
- High Private Use Surrogates
- Low Surrogates
- Private Use Area
- Variation Selectors
- Shorthand Format Controls
- Tags
- Variation Selectors Supplement
- Supplementary Private Use Area-A
- Supplementary Private Use Area-B
