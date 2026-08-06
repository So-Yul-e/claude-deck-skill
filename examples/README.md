# Examples

`build_catalog.py` generates one PPTX with exactly 20 representative deck builder pages:

cover, section, statement, cards, bullets, table, deflist, tree, flow, timeline, bar, column, donut, progress, matrix, shots, compare, quote, stat, and gate.

Run from the repository root:

```bash
DECK_PY="$(bash deck/scripts/deps-macos.sh --python)"
"$DECK_PY" examples/build_catalog.py examples/output/deck-builder-catalog.pptx
bash deck/scripts/render-macos.sh \
  examples/output/deck-builder-catalog.pptx \
  examples/output/deck-builder-catalog.pdf
```

The script expects the installable `deck/` skill directory to contain `scripts/deck.py` and its Python dependencies. It creates temporary screenshot fixtures with Pillow for the `shots` slide and removes those fixtures automatically when the process exits.

The committed PPTX, PDF, and contact sheet under `examples/output/` are the
macOS validation artifacts. Windows CI rebuilds the PPTX; physical Windows PDF
export remains beta until target-machine evidence is added.
