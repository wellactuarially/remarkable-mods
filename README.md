# remarkable-mods

## floating-layers: per-preset layers for FouzR's floating toolbar

A fork of [FouzR's floating toolbar](https://github.com/FouzR/xovi-extensions) (`floating.qmd`) for xovi + qt-resource-rebuilder.
Each full pen preset on the bar saves the layer you were on when you added it. Tapping the preset switches pen *and* layer.
If the page doesn't have that layer, only the pen changes; no layer is created. Presets saved before the patch keep working
and never switch layer.

| File | What it is |
| --- | --- |
| `3.28/floating-layers.qmd` | Ready-to-install mod: FouzR's 3.28 `floating.qmd` (commit `f63bbc5`, sha256 `1c2ea2f56f9619d1b2bff08667c2430c7ac051c061632710f0f7fdfa022b6c09`) with the patch applied |
| `patch_floating_layers.py` | Regenerates the mod from FouzR's file; stops if any of its 8 anchors doesn't match exactly |
| `check_hashtab.py` | Checks a hashed `.qmd` against a tablet's hashtab and lists names missing on that firmware |

Both scripts need only the Python 3 standard library.

### Status

- 3.28: patch applies cleanly; bracket balance unchanged from the original. All layer API names it uses
  (`sceneController`, `currentLayer`, `setCurrentLayer`, `addLayer`, `sceneLayersModel`, `isWritingTool`) are hashed
  in FouzR's or rmitchellscott's 3.28/3.29 mods, so they exist on those firmwares.
- Not yet done: a qmldiff parse check, and any on-device test.
- 3.29: no FouzR build exists; the 3.28 output is the candidate. Check it with `check_hashtab.py` first.
- 3.22–3.27: the patch script refuses FouzR's files for these versions; it would need a port.

### Regenerate

```sh
git clone https://github.com/FouzR/xovi-extensions
python3 patch_floating_layers.py xovi-extensions/3.28/floating.qmd 3.28/floating-layers.qmd
```

### Check against your firmware (do this on 3.29)

```sh
ssh root@<tablet-ip> /home/root/xovi/rebuild_hashtable
scp root@<tablet-ip>:/home/root/xovi/exthome/qt-resource-rebuilder/hashtab .
python3 check_hashtab.py hashtab 3.28/floating-layers.qmd --unhash floating-layers.readable.txt
```

`[ok]` means every name exists on that firmware. Run it on FouzR's unpatched file too: if that fails as well, the break is FouzR's, not the patch's.

### Install

1. Back up `/home/root/quickTool.json`, `quickTool2.json` and `quickTool3.json`.
2. Remove FouzR's `floating.qmd` from `/home/root/xovi/exthome/qt-resource-rebuilder/` (or uninstall it in Vellum). Both patch the same code.
3. Copy `floating-layers.qmd` into that folder and restart xovi.

Don't run it alongside rmitchellscott's `penLayerMemory.qmd`. Roll back by deleting `floating-layers.qmd` and restarting xovi.

### License

GPL-3.0, as the original (see `LICENSE`).
