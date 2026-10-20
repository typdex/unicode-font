# Additional font research

Evaluation baseline: **Unicode 18.0.0**. The original 271 files left **82,534 targets** unmapped. Adding 387 files (804 faces) resolves **80,191**; **2,343** remain.

Counts below intersect actual font cmaps with the fixed original missing-code-point set. Contributions overlap and must not be added. A zero result means the font adds alternatives but fills no gap from that baseline.

| Added font | Unicode baseline | Non-FOSS | Commercial use | Previously missing targets mapped | Unique among added fonts |
| --- | --- | --- | --- | ---: | ---: |
| [Typdex Jigmo2 U18 / Regular](https://github.com/kamichikoichi/jigmo/tree/a6893b2278e39747fc3476465f7fcacf0126bca8) | 18.0.0 | No | permitted-with-license-conditions | 53,419 | 0 |
| [Jigmo2 / Regular](https://kamichikoichi.github.io/jigmo/Jigmo-20250912.zip) | 18.0.0 | No | permitted-with-license-conditions | 53,419 | 0 |
| [BabelStone Han / Regular](https://www.babelstone.co.uk/Fonts/Download/BabelStoneHan-16.0.3.zip) | 18.0.0 | No | permitted-with-license-conditions | 27,372 | 0 |
| [Typdex Jigmo3 U18 / Regular](https://github.com/kamichikoichi/jigmo/tree/a6893b2278e39747fc3476465f7fcacf0126bca8) | 18.0.0 | No | permitted-with-license-conditions | 12,343 | 0 |
| [Jigmo3 / Regular](https://kamichikoichi.github.io/jigmo/Jigmo-20250912.zip) | 18.0.0 | No | permitted-with-license-conditions | 12,318 | 0 |
| [Seal Sans / Regular](https://raw.githubusercontent.com/Ghimist/seal-sans/9372f0813770a605ec5ee068fc48660b231b3427/SealSans-Regular_v1.otf) | 18.0.0 | No | permitted-with-license-conditions | 11,328 | 11,303 |
| [Heiti TC / Light](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 3,859 | 0 |
| [Heiti SC / Light](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 3,859 | 0 |
| [Heiti TC / Medium](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 3,859 | 0 |
| [Heiti SC / Medium](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 3,859 | 0 |
| [Egyptology Extended / Regular](https://raw.githubusercontent.com/LumabyteCo/egyptology-extended-font/015a15f0e8ddced9061fd2f715ca49f5407d4d91/fonts/EgyptologyExtended.ttf) | 18.0.0 | No | permitted-with-license-conditions | 2,924 | 2,924 |
| [Typdex Jigmo U18 / Regular](https://github.com/kamichikoichi/jigmo/tree/a6893b2278e39747fc3476465f7fcacf0126bca8) | 18.0.0 | No | permitted-with-license-conditions | 151 | 151 |
| [Fairfax HD / Medium](https://raw.githubusercontent.com/kreativekorp/open-relay/e4b81241e8c7269a91c0bd865cf5c9e7208fbada/FairfaxHD/FairfaxHD.ttf) | 18.0.0 | No | permitted-with-license-conditions | 51 | 51 |
| [Songti SC / Bold](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |
| [Songti TC / Bold](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |
| [Songti SC / Light](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |
| [STSong / Regular](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |
| [Songti TC / Light](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |
| [Songti SC / Regular](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |
| [Songti TC / Regular](https://support.apple.com/en-us/122869) | 18.0.0 | Yes | subject-to-platform-and-font-license | 5 | 0 |

Measured faces that fill no original gap: apple-macos: 774; charis: 8; jigmo: 1; tangut-yinchuan: 1.


## Results for each originally incomplete block

| Block | Unicode baseline | Previously missing | Resolved | Still missing |
| --- | --- | ---: | ---: | ---: |
| Archaic Cuneiform Numerals | 18.0.0 | 311 | 0 | 311 |
| Egyptian Hieroglyphs Extended-A | 18.0.0 | 3,995 | 2,924 | 1,071 |
| Tangut | 18.0.0 | 8 | 8 | 0 |
| Tangut Supplement | 18.0.0 | 24 | 24 | 0 |
| Tangut Components Supplement | 18.0.0 | 115 | 115 | 0 |
| Jurchen | 18.0.0 | 914 | 4 | 910 |
| Jurchen Radicals | 18.0.0 | 51 | 0 | 51 |
| Latin Extended-G | 18.0.0 | 51 | 51 | 0 |
| CJK Unified Ideographs Extension B | 18.0.0 | 35,883 | 35,883 | 0 |
| CJK Unified Ideographs Extension C | 18.0.0 | 4,047 | 4,047 | 0 |
| CJK Unified Ideographs Extension E | 18.0.0 | 5,579 | 5,579 | 0 |
| CJK Unified Ideographs Extension F | 18.0.0 | 7,423 | 7,423 | 0 |
| CJK Compatibility Ideographs Supplement | 18.0.0 | 487 | 487 | 0 |
| CJK Unified Ideographs Extension G | 18.0.0 | 4,296 | 4,296 | 0 |
| CJK Unified Ideographs Extension H | 18.0.0 | 4,170 | 4,170 | 0 |
| CJK Unified Ideographs Extension J | 18.0.0 | 3,852 | 3,852 | 0 |
| Seal | 18.0.0 | 11,328 | 11,328 | 0 |

## Locate a font for a specific character

[gap-resolution.csv](gap-resolution.csv) gives exact ranges, the Unicode version in which each character was introduced, and every added font that maps the range. Adjacent code points are grouped only when their block, character age and font candidates all match. Font IDs join to [fonts.csv](fonts.csv) for download URLs, archive members, licenses and hashes.

```sh
python3 scripts/query.py --codepoint U+20000 --limit 0
python3 scripts/query.py --codepoint U+13460 --limit 0
```

Remaining gaps are in [gaps.md](gaps.md). Unmeasured or rejected leads and license caveats are recorded in [research-notes.md](../docs/research-notes.md). Measured cmap support does not establish outline or shaping quality.
