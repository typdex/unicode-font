# Apple-distributed font survey

Measured **785 faces in 368 installed files** from **macOS 27.0.1, build 26A434**. Evaluation baseline: **Unicode 18.0.0**.

Their union maps **3,864 originally missing targets**. Of these, **0** are absent from all other fonts in the expanded survey.

This is the installed snapshot on the research machine, not a claim that every Apple downloadable font or every Apple platform has been surveyed. [Apple’s published font inventory](https://support.apple.com/en-us/122869) and [developer font page](https://developer.apple.com/fonts/) are discovery references; embedded font versions and locked file hashes identify the measured bytes.

The measured Apple Color Emoji is version **22.0d3e2** and Apple Symbols is **22.0d3e1**. Their font release numbers are not Unicode-version claims.

All collection faces are measured. Apple-distributed fonts include third-party fonts and OFL fonts: the latter are classified per face using explicit embedded license grants. The remaining fonts retain their platform/vendor terms. [fonts.csv](fonts.csv) has the version, collection face, non-FOSS and commercial-use columns.

**LastResort.otf is excluded**: its cmap maps Unicode positions to generic block symbols, which would falsely inflate character coverage. No Apple font binaries are redistributed.

| Originally incomplete block | Unicode baseline | Original gaps mapped by Apple fonts |
| --- | --- | ---: |
| Archaic Cuneiform Numerals | 18.0.0 | 0 |
| Egyptian Hieroglyphs Extended-A | 18.0.0 | 0 |
| Tangut | 18.0.0 | 0 |
| Tangut Supplement | 18.0.0 | 0 |
| Tangut Components Supplement | 18.0.0 | 0 |
| Jurchen | 18.0.0 | 0 |
| Jurchen Radicals | 18.0.0 | 0 |
| Latin Extended-G | 18.0.0 | 0 |
| CJK Unified Ideographs Extension B | 18.0.0 | 3,858 |
| CJK Unified Ideographs Extension C | 18.0.0 | 0 |
| CJK Unified Ideographs Extension E | 18.0.0 | 0 |
| CJK Unified Ideographs Extension F | 18.0.0 | 0 |
| CJK Compatibility Ideographs Supplement | 18.0.0 | 6 |
| CJK Unified Ideographs Extension G | 18.0.0 | 0 |
| CJK Unified Ideographs Extension H | 18.0.0 | 0 |
| CJK Unified Ideographs Extension J | 18.0.0 | 0 |
| Seal | 18.0.0 | 0 |

To remeasure a compatible licensed macOS installation:

```sh
.venv/bin/python scripts/refresh.py --rescan-local
```

If the OS changed its font bytes, inspect the changes before accepting a new lock. Ordinary refreshes reuse the committed local-font evidence, so the public catalog can be rebuilt on Linux without the proprietary binaries.

## Separate Apple developer downloads

Apple’s [current developer font page](https://developer.apple.com/fonts/) also offers SF Pro, SF Compact, SF Mono, New York and script extensions. Those downloadable packages were reviewed as discovery and license references, not measured as additional binaries. Their download license limits use to specified Apple-interface design purposes; do not substitute those terms for the terms of an installed platform font. The catalog’s commercial-use column therefore retains a platform/font-license condition rather than a blanket commercial-use grant.
