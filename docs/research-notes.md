# Research notes and unresolved leads

This round checks binaries against the **82,534 missing targets** in the original
271-file Unicode 18.0.0 survey. The measured counts in
[additional-fonts.md](../reports/additional-fonts.md) take precedence over
upstream marketing totals, which can count glyphs, sequences or PUA characters.

| Candidate | Decision and evidence |
| --- | --- |
| [Jigmo 20250912](https://kamichikoichi.github.io/jigmo/) | Measured all three CC0 fonts. Jigmo2 and Jigmo3 fill the large CJK extension gaps. Its release advertises Unicode 17 support; character age and the Unicode 18 evaluation baseline are separate columns. |
| [BabelStone Han 16.0.3](https://www.babelstone.co.uk/Fonts/Han.html) | Measured the versioned release. Adds alternatives for 27,372 original missing targets, overlapping Jigmo. Uses the original Arphic Public License; the later noncommercial Arphic license does not apply to this release. |
| [Egyptology Extended](https://github.com/LumabyteCo/egyptology-extended-font) | Measured the pinned TTF under its CeCILL-2.1 declaration. It maps 2,924 original missing targets, rather than completely covering Extended-A. The README's counts differ from the actual scalar cmap; preserve this discrepancy. |
| [Seal Sans](https://github.com/Ghimist/seal-sans) | Measured all 11,328 Seal targets. License is declared as GNU AGPL v3.0 in the font's embedded name record 13; its embedded LICENSE URL is missing from the repository. Retain that provenance caveat. The author describes the outlines as provisional. |
| [Fairfax HD](https://www.kreativekorp.com/software/fonts/fairfaxhd/) | Measured the main TTF from a pinned source commit under OFL-1.1. Fills the remaining 51 Latin Extended-G targets. Other family variants were not measured. |
| [Charis 7.000](https://software.sil.org/charis/download/) | Measured all eight TTF faces under OFL-1.1. Adds no original missing target; retained as evidence that a plausible phonetic candidate need not close a Unicode 18 gap. |
| [Tangut Yinchuan 16.004](https://www.babelstone.co.uk/Fonts/Yinchuan.html) | Included as a permitted-use, non-FOSS research entry. Free download/use is granted; modification, sale and for-profit font redistribution require express permission. Publication acknowledgement is requested. Commercial document use and commercial font redistribution are recorded separately. This older binary does not fill the surveyed newer Tangut gaps. |
| [Apple-distributed fonts](../reports/apple-fonts.md) | Measured installed macOS 27.0.1 build 26A434 files. Their versions and licenses are recorded per face; LastResort is excluded as diagnostic fallback. Some Apple-distributed faces explicitly carry OFL grants. No Apple binaries are redistributed. |
| [Kaiyuan Small Seal](https://github.com/frankslin/kaiyuan-small-seal-font) | OFL project with no released font at the inspected revision. Keep as a development lead; do not count a target repertoire as measured coverage. |
| [Alari Xuwasun Jurchen](https://fonts.zeoseven.com/items/2403/) | A distributor lists OFL-1.1 and Unicode Jurchen samples. The author's site is linked, but a verifiable original font download and its accompanying license were not retrieved in this session. Not counted as measured coverage. |
| [BabelStone Jurchen scan fonts](https://www.babelstone.co.uk/Fonts/index.html) | Listed as PUA-mapped. Similar glyph shapes in PUA do not establish Unicode 18 Jurchen mappings. Not counted as closing those scalar gaps. |
| [PC-all / PCSL](https://oracc.museum.upenn.edu/pcsl/signlist/ACNConcordance/index.html) | Primary sign-list material points to a proto-cuneiform font. Its download timed out, and this session did not verify a font license. Keep as a lead for Archaic Cuneiform Numerals, without adding speculative coverage. |

The experimental [Jigmo Unicode 18 build](../experiments/jigmo/README.md) adds
available GlyphWiki outlines to the published CC0 fonts. It records every
requested scalar, fetched SVG hash, unavailable outline and resulting font hash.
Its scope and incomplete glyph availability are reported separately from the
published Jigmo release. It is not a claim of complete Unicode 18 rendering.
