# Highlight-Coding Annotation UI

The highlight-coding editor is a token-level annotation surface for inspecting
several dimensions of a code-switching analysis without making colour carry the
whole meaning. Each token box combines colour with text, glyphs, borders,
underlines, and markers.

The six modes are: language, 4-M type, switch type, trigger role, mixed-code
span, and integration-score band. Language mode uses the project palette and a
language glyph. 4-M mode uses underline styles. Switch type uses solid, dashed,
or dotted borders. Trigger mode adds arrows: `↦` for a trigger candidate and `←`
for a triggered token. Mixed-code span membership uses a faint span treatment.
Integration score mode groups non-host stems into high, mid, and low bands.

Keyboard navigation is designed to work without a mouse: left/right moves token
focus, Shift+left/right extends selection, Alt+left/right jumps language
boundaries, Ctrl+left/right jumps switch points, `L` opens language mode, `M`
opens 4-M mode, `T` toggles trigger-role work, Space plays audio at the focused
token timestamp, Ctrl+Z undoes, Ctrl+Shift+Z redoes, and Esc clears selection.
Shortcuts are remappable through `gui/keymap.yaml`.

Multi-select supports Shift-click contiguous spans and Ctrl-click individual
tokens. The bulk-edit menu can set language, Matrix/Embedded Language, 4-M type,
switch type, trigger role, custom tags, and memos. Bulk edits are atomic: either
all selected tokens are updated or none are. Undo restores the previous token
state.

Accessibility is built into the representation. Each token exposes an accessible
name such as `manager language eng matrix zul 4-M content switch intra trigger
trigger`. High-contrast theme and font scaling are supported by the widget layer.
The editor uses QGraphicsView item culling so long utterances remain responsive
on modest hardware.

Text diagram:

```text
[ ● sawubona ] [ ▲ manager ↦ ] [ ● uyasebenza ]
  language+glyph   trigger arrow      language+glyph
  border=switch    underline=4-M      hatching=mixed span
```
