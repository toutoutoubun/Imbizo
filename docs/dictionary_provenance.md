# Dictionary Provenance and Reproducibility

The dictionary bootstrap subsystem lets Imbizo-CS rebuild imported dictionaries from audited source files. It is intentionally separate from the runtime application: once the dictionaries have been built, Imbizo-CS can run in an air-gapped environment with no network access.

For the combined dictionary and processing-resource provenance guide, see
`docs/resource_provenance.md`. This older page is retained as the dictionary
specific view for existing links.

## Citing Imported Dictionaries

When you use imported dictionaries in a thesis or article, cite both Imbizo-CS and the source dictionary. A methods section should also name the dictionary YAML file, content version, retrieval date, raw SHA-256 hash, and adapter version recorded in the YAML header.

Suggested BibTeX templates:

```bibtex
@dataset{up_multilingual_lexicons,
  title = {South African multilingual lexicons},
  author = {{University of Pretoria ABSA Chair for Data Science}},
  year = {2024},
  publisher = {University of Pretoria Research Data Repository},
  note = {Retrieved and converted by Imbizo-CS dictionary bootstrap}
}

@software{mafoko_za_mavito,
  title = {za-mavito},
  author = {{Data Science for Social Impact}},
  year = {2024},
  url = {https://github.com/dsfsi/za-mavito},
  note = {Cite the exact Git commit used in your bootstrap bundle}
}

@dataset{african_wordnet_sadilar,
  title = {African Wordnet},
  author = {{UNISA SADiLaR node}},
  url = {https://repo.sadilar.org/},
  note = {Cite the SADiLaR handle and XML file checksum used}
}

@dataset{unisa_termbank,
  title = {UNISA Multilingual Linguistic Terminology},
  author = {{UNISA SADiLaR node}},
  url = {https://repo.sadilar.org/},
  note = {Cite the SADiLaR handle and Lexonomy export checksum used}
}

@misc{exdn_macvicar_1935,
  title = {English-Xhosa Dictionary for Nurses},
  author = {MacVicar},
  year = {1935},
  note = {Public-domain historical source; cite also the linked-data conversion used}
}
```

## Rebuilding the Dictionaries

On a connected machine, run:

```bash
python tools/make_bundle.py --out bootstrap_bundle.zip
```

Move the zip to the offline machine and run:

```bash
python tools/bootstrap.py --offline --from-bundle bootstrap_bundle.zip
```

The build records are written under `dictionaries/imported/_provenance/`. The raw-file SHA-256 values in those records should match the bundle checksums.

## Methods-Section Wording

You may write: "Dictionary suggestions were generated from locally stored Imbizo-CS imported dictionaries. Each imported file recorded source URL, license, retrieval date, raw SHA-256 checksum, transformation adapter, and adapter version. All imported entries were treated as unverified suggestions until reviewed in the project context."
