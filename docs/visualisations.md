# Visualisations: Heatmaps and Sankey Diagrams

Imbizo-CS renders visualisations locally so that a researcher can include figures
in a thesis, article, or supervision memo without uploading data to a remote
service. The v2.0-oriented Speaker & Scene Profile uses two figure types:
speaker-scene heatmaps and language-transition Sankey diagrams.

A heatmap answers a basic distributional question: in each scene, which language
dominates each speaker's tokens? In a fictional isiZulu-English interview, the
formal interview scene might show Speaker S01 using mostly isiZulu with a few
English technical nouns, while an informal aside might show more English. The
heatmap does not interpret that shift. It gives the researcher a reproducible
view of where to look more closely. Every cell displays a glyph, a language
code, and a proportion, so the meaning is not carried by colour alone.

A Sankey diagram answers a different question: which language-to-language
transitions occur over time? If an utterance moves from isiZulu to English and
back to isiZulu, the Sankey counts `zul -> eng` and `eng -> zul` flows. Ribbon
width is proportional to transition count. The source and target ends both carry
language labels and glyphs. This makes the figure usable in grayscale printouts
and for colour-blind readers.

The default palette follows Wong's colourblind-safe palette (Wong, 2011). If a
project has more languages than the palette has distinctive colours, Imbizo-CS
keeps assigning deterministic glyphs and lets the researcher edit `palette.yaml`
inside the project folder. Palette edits are project-local and reproducible.

Both figure types include a footer with the project name, generation timestamp,
Imbizo-CS version, dictionary versions where available, and a reference to
`PRINCIPLES.md`. SVG outputs embed text as paths so a collaborator opening the
file on another offline machine does not need the same fonts installed. PNG and
SVG exports are written under the local project folder, usually in
`exports/figures/`.

Use these figures as prompts for interpretation, not as interpretations
themselves. A high English proportion in one scene might reflect topic, role,
quotation, technical vocabulary, or local stance-taking. The figure shows the
pattern; the researcher supplies the reading.

Reference: Wong, B. (2011). Color blindness. *Nature Methods*, 8, 441.
