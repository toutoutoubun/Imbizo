# Dictionary Bootstrap Subsystem

The bootstrap subsystem is the only part of Imbizo-CS allowed to fetch external dictionary sources. It creates local YAML dictionaries under `dictionaries/imported/` and records provenance so the runtime workbench remains offline-first.

```text
bootstrap/
└── sources.yaml                       # master source manifest
tools/
├── bootstrap.py                       # fetch or unpack, verify, convert
├── make_bundle.py                     # create air-gap zip
├── check_compliance.py                # CI checks for headers, licenses, verification state
└── adapters/
    ├── base.py                        # SourceAdapter ABC
    ├── utils/nc_hints.py              # minimal noun-class prefix hints
    ├── utils/provenance.py            # standard header and SHA-256 helpers
    ├── up_lexicons.py                 # UP multilingual lexicon adapter
    ├── mafoko.py                      # Mafoko CSV adapter
    ├── african_wordnet.py             # SADiLaR African Wordnet XML adapter
    ├── unisa_termbank.py              # UNISA Lexonomy terminology adapter
    └── exdn.py                        # EXDN Turtle/RDF adapter
LICENSES/                              # license text for imported sources
dictionaries/imported/                 # generated dictionaries; gitignored except provenance anchors
downloads/raw/                         # downloaded raw files; gitignored
tests/test_adapter_*.py                # synthetic adapter tests
```

Each adapter reads an already-downloaded file and writes one or more YAML files. Adapters never make network calls.
