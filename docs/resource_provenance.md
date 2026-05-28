# Resource Provenance and Reproducibility

Imbizo-CS bootstrap resources include imported dictionaries and processing
resources. Both use the same provenance discipline: source URL, license,
retrieval date, SHA-256 checksum, adapter path, and adapter version are recorded
in local YAML or JSON files. The runtime application does not contact the
network.

## Reproducing a Build

On a connected machine:

```bash
python tools/make_bundle.py --out bootstrap_bundle.zip
```

Move the zip by USB or other local media, then on the offline machine:

```bash
python tools/bootstrap.py --offline --from-bundle bootstrap_bundle.zip
```

For optional ASR:

```bash
IMBIZO_ASR_ACCEPTED=1 python tools/bootstrap.py --offline --from-bundle bootstrap_bundle.zip --include-asr
```

The bootstrap writes provenance under `dictionaries/imported/_provenance/`,
including `dictionaries/imported/_provenance/processing/` for models, corpora,
datasets, and toolkits.

## Suggested BibTeX

```bibtex
@inproceedings{joulin2017fasttext,
  title = {Bag of Tricks for Efficient Text Classification},
  author = {Joulin, Armand and Grave, Edouard and Bojanowski, Piotr and Mikolov, Tomas},
  booktitle = {EACL},
  year = {2017}
}

@inproceedings{eiselen2014nchlt,
  title = {Developing Text Resources for Ten South African Languages},
  author = {Eiselen, Roald and Puttkammer, Martin J.},
  booktitle = {LREC},
  year = {2014}
}

@article{gaustad2024morph,
  title = {Updated Morphologically Annotated Corpora for South African Languages},
  author = {Gaustad, Tanja and McKellar, Cindy},
  journal = {Journal of Open Humanities Data},
  year = {2024}
}

@inproceedings{dione2023masakhapos,
  title = {MasakhaPOS: Part-of-Speech Tagging for Typologically Diverse African Languages},
  author = {Dione, Cheikh M. Bamba and others},
  booktitle = {ACL},
  year = {2023}
}

@inproceedings{adelani2022masakhaner,
  title = {MasakhaNER 2.0: Africa-centric Transfer Learning for Named Entity Recognition},
  author = {Adelani, David Ifeoluwa and others},
  booktitle = {EMNLP},
  year = {2022}
}

@misc{za_lex,
  title = {ZA_LEX lexical pronunciation resources},
  author = {van Niekerk, Daniel and ttslab},
  url = {https://github.com/ttslab/za_lex},
  note = {Cite the exact commit hash and preserved per-language LICENCE files used}
}

@software{whisper_cpp,
  title = {whisper.cpp},
  author = {Gerganov, Georgi and ggml-org contributors},
  url = {https://github.com/ggml-org/whisper.cpp},
  note = {Optional ASR component; cite exact tag, model file, and model checksum}
}
```

## Methods-Section Wording

You may write: "Processing resources were installed from an Imbizo-CS bootstrap
bundle. Each installed model, corpus, dataset, or toolkit recorded source URL,
license, retrieval date, raw SHA-256 checksum, transformation adapter, and
adapter version. Automated outputs were treated as unverified suggestions and
manually reviewed in the project context."

## Licence Inheritance: What Your Outputs Carry From Your Inputs

Imbizo-CS is AGPLv3 software, but the resources it reads are not all AGPLv3.
Some are dictionaries under CC-BY, some are corpora under attribution licences,
some are NonCommercial datasets, and some may be community-governed overlays.
That difference matters because a thesis chapter, a CSV export, a tagged corpus,
and a redistributed model file are not the same kind of output.

Aggregation means Imbizo-CS stores or uses an independent resource alongside the
software without turning that resource into AGPLv3 source code. The fastText
model, NCHLT corpora, and Masakhane datasets are treated this way. Combination
means a resource can be processed as part of the normal software distribution
without a known incompatibility, while still preserving attribution. A derivative
or adapted resource is different again: if you redistribute a tagged corpus that
directly incorporates labels from a NonCommercial dataset, those data-layer terms
may travel with the exported corpus even though your prose discussion remains
your own scholarly work.

Concrete example: if you analysed isiZulu-English interviews using MasakhaPOS
tags, your published numerical findings are not automatically CC-BY-NC. You can
write a thesis chapter about the findings. But if you share a supplementary CSV
containing MasakhaPOS-derived POS labels for each token, that supplementary file
should retain the CC-BY-NC notice and attribution. If you share only your raw
interview transcript and your manual annotations, the MasakhaPOS notice may not
apply to that raw transcript, though your methods section should still say that
POS suggestions were consulted.

Decision flowchart:

```text
Did your output include copied resource content or model/data-derived labels?
  No  -> Cite Imbizo-CS and the resources used in methods; your prose remains yours.
  Yes -> Did any source have Tier-2 NonCommercial or ShareAlike terms?
          No  -> Preserve attribution and provenance in the export.
          Yes -> Keep the report footer notice; avoid commercial redistribution
                 unless you have separate permission or legal advice.
        Did any source have Tier-3 community governance terms?
          Yes -> Share through the community-review path and preserve local caveats.
```

When unsure, export with the licence-propagation footer enabled and include the
project's `dictionaries/imported/_provenance/` directory in your archive.

## Bootstrap Resource Licence Summary

| Resource | Licence | Tier | AGPLv3 combinable? | Commercial use? | ShareAlike? | Default install? |
| --- | --- | --- | --- | --- | --- | --- |
| UP Multilingual Lexicons | CC-BY-4.0 | 1 | combination | yes | no | yes |
| Mafoko / za-mavito | NOODL or CC-BY-NC-SA-2.5-ZA | 3 | aggregation only | restricted where NC rows apply | yes where SA rows apply | no |
| African Wordnet verified subset | CC-BY-4.0 | 1 | combination | yes | no | yes |
| UNISA Termbank | Per-file SADiLaR metadata; converted files resolve to CC-BY-4.0 or OER-UNISA when verified | 1 for converted files only | combination after per-file verification | yes for converted Tier-1 files | no for converted Tier-1 files | yes, but unknown / NC files are skipped |
| EXDN | Public Domain | 1 | combination | yes | no | yes |
| fastText lid.176 compressed | CC-BY-SA-3.0 | 2 | aggregation only | yes | yes | no |
| fastText lid.176 full | CC-BY-SA-3.0 | 2 | aggregation only | yes | yes | no |
| NCHLT Text Corpora | CC-BY-2.5-SA | 1 | aggregation only | yes | no | yes |
| Morphologically Annotated Corpora | CC-BY-4.0 when verified | 1 | combination | yes | no | yes |
| MasakhaPOS | CC-BY-NC-4.0 | 2 | aggregation only | no | no | no |
| MasakhaNER | CC-BY-NC-4.0 | 2 | aggregation only | no | no | no |
| ZA_LEX | Apache-2.0 / MIT plus per-language files | 1 | combination | yes | no | yes |
| whisper.cpp source | MIT | 1 | combination | yes | no | no, ASR opt-in |
