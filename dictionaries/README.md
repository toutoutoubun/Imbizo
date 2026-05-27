# Imbizo-CS Dictionary Layers

Imbizo-CS loads dictionaries in layers so imported material never overrides a researcher's judgement.

## Layers

1. `project/` contains project-local decisions and overrides. This is the highest-priority layer because the researcher knows the corpus context.
2. `community/` contains curated overlays shared through offline community-review packets.
3. `user_overrides/` contains local additions a researcher wants to reuse across projects.
4. `imported/` contains automatically converted external sources created by `tools/bootstrap.py`.
5. `builtin/` contains small hand-written starter dictionaries shipped with Imbizo-CS.

Only `imported/` is populated by the bootstrap subsystem. Every imported entry starts with `verified: false`, because conversion from an external source is not the same as scholarly validation in a particular interview context.

## Imported Dictionary Provenance

Each YAML file in `imported/` carries a standard header with source URL, license, retrieval date, raw SHA-256 checksum, adapter path, and adapter version. Additional build records live in `imported/_provenance/`.

To inspect an entry's provenance, open the YAML file and read the `source:` block above `entries:`. That block is designed to be copyable into a methods appendix.

## Overrides

Do not edit imported YAML directly. Instead, create a project-local override in the project folder. Project-local overrides preserve the original imported source and make the interpretive decision explicit in provenance.

## Sharing Curated Overlays

When a community reviewer improves or disputes an imported entry, export the change as a community-review packet. The packet contains a human-readable diff, a machine-readable diff, and a signature hash, so it can travel by USB and be reviewed without internet access.

## Why `verified: false` Is the Default

External dictionaries are useful starting points, but code-switching analysis depends on setting, speaker, genre, orthography, and community knowledge. Imbizo-CS therefore treats imported entries as suggestions until a human researcher or reviewer verifies them.
