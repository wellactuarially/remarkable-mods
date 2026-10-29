#!/usr/bin/env python3
"""
Adds per-preset layers to FouzR's floating toolbar (floating.qmd).

Each full pen preset on the floating bar (tool + colour + thickness) also
remembers the layer you were on when you added it. Tapping the preset
switches pen *and* layer, if that layer exists on the current page (otherwise
only the pen changes). Presets saved before this patch keep working and
simply don't change layer.

Usage:
    python3 patch_floating_layers.py <path/to/floating.qmd> [output.qmd]

The script only edits text it can find exactly; if FouzR's file has changed
shape in a newer version, it stops and tells you which edit failed instead
of producing a broken mod.

Based on floating.qmd by FouzR (https://github.com/FouzR/xovi-extensions),
GPL-3.0. This patch and its output are GPL-3.0 as well.
"""
import re
import sys

# Hashed identifiers used by FouzR's file (qmldiff djb2 hashes, seed 5481).
H = {
    "item": "~&6503936152&~",
    "modelData": "~&254539508423767444&~",
    "documentViewTools": "~&7842069035455457876&~",
    "activePen": "~&254522140932088040&~",
    "thickness": "~&254549061334391125&~",
    "capture": "~&233723474542109&~",
    "pointSize18": "~&6503823200&~.pointSize: 18",
    "white": '~&"214646069354&~',
    "black": '~&"214621299494&~',
}

DVT_THICK = f"{H['documentViewTools']}.{H['activePen']}.{H['thickness']}"

HELPERS = """
				/* --- per-preset layers (patch) --- */
				function currentLayerIndex() {
					return sceneController ? sceneController.currentLayer : -1;
				}
				function presetLayerMatches(m) {
					if (m.presetLayer === undefined || m.presetLayer === null || m.presetLayer < 0) return true;
					return !!sceneController && sceneController.currentLayer === m.presetLayer;
				}
				function applyPresetLayer(target) {
					if (target === undefined || target === null || target < 0 || !sceneController) return;
					var layerCount = 1;
					try { layerCount = Math.max(sceneLayersModel.count, 1); } catch (e) {}
					if (target >= layerCount) return;
					if (sceneController.currentLayer !== target) sceneController.setCurrentLayer(target);
				}
				/* --- end per-preset layers --- */
"""

BADGE = """
						Text {
							anchors.bottom: parent.bottom
							anchors.right: parent.right
							rightPadding: 4
							bottomPadding: 2
							text: "L" + (modelData.presetLayer + 1)
							visible: modelData.presetLayer !== undefined && modelData.presetLayer !== null && modelData.presetLayer >= 0 && documentViewTools.isWritingTool(modelData.tool) && modelData.type != "Tool" && modelData.type != "Thick" && modelData.type != "Colour" && !timeOutBeforeMovingTools
							color: (parent && parent.selected) ? "white" : "black"
							font.family: "Helvetica"
							font.weight: Font.Bold
							font.pointSize: 11
						}"""


def edit(s, name, pattern, repl, count, regex=False, occurrence=None):
    """Apply one edit; fail loudly if the anchor isn't found exactly `count` times."""
    found = len(re.findall(pattern, s)) if regex else s.count(pattern)
    if found != count:
        sys.exit(f"[x] edit '{name}': expected {count} match(es), found {found}. "
                 "This floating.qmd differs from the one the patch was written for.")
    if occurrence is not None:  # replace only the Nth (0-based) occurrence
        idx = -1
        for _ in range(occurrence + 1):
            idx = s.index(pattern, idx + 1)
        return s[:idx] + repl + s[idx + len(pattern):]
    if regex:
        return re.sub(pattern, repl, s)
    return s.replace(pattern, repl)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace(".qmd", "-layers.qmd")
    s = open(src, encoding="utf-8").read()

    if "per-preset layers (patch)" in s:
        sys.exit("[x] This file is already patched.")

    # 1. Helper functions on the floating bar object.
    s = edit(s, "helpers", "\t\t\t\tfunction addNewTool(", HELPERS + "\t\t\t\tfunction addNewTool(", 1)

    # 2. A new full preset records the current layer.
    #    (Insert a field at the end of the object pushed inside addNewTool.)
    m = re.search(r"function addNewTool\([^)]*\)\s*\{.*?(\n[ \t]*\}\)\s*\n[ \t]*quickToolChanged\(\))", s, re.S)
    if not m:
        sys.exit("[x] edit 'record layer': couldn't find the object pushed in addNewTool().")
    at = m.start(1)
    s = s[:at] + ",\n\t\t\t\t\t\tpresetLayer: currentLayerIndex()" + s[at:]

    # 3. Tapping a full preset switches to its layer (2nd copy = full-preset branch;
    #    the 1st is the tool-only branch, which keeps the current layer).
    tap = f"{DVT_THICK} = {H['modelData']}.{H['thickness']};}}"
    s = edit(s, "apply layer on tap", tap,
             f"{DVT_THICK} = {H['modelData']}.{H['thickness']};\n"
             "\t\t\t\t\t\t\t\t\t\t\tfloatQuick.applyPresetLayer(modelData.presetLayer);}",
             2, occurrence=1)

    # 4. A preset only shows as selected when you're also on its layer.
    sel = f"{DVT_THICK} === {H['modelData']}.{H['thickness']}):\n"
    s = edit(s, "selected state", sel,
             f"{DVT_THICK} === {H['modelData']}.{H['thickness']} && floatQuick.presetLayerMatches(modelData)):\n", 1)

    # 5. Thickness label colour follows the same rule (else it turns white on a light button).
    lbl = f"{DVT_THICK} === {H['modelData']}.{H['thickness']}) ? {H['white']}:{H['black']} ):("
    s = edit(s, "label colour", lbl,
             f"{DVT_THICK} === {H['modelData']}.{H['thickness']} && floatQuick.presetLayerMatches(modelData)) ? {H['white']}:{H['black']} ):(", 1)

    # 6. Long-press toggle (add/remove) removes only the preset on the current layer.
    rm = (rf"({re.escape(H['item'])}\.{re.escape(H['thickness'])} == "
          rf"{re.escape(DVT_THICK)})(\s*\n\s*\))")
    s = edit(s, "remove matches layer", rm, r"\1 && floatQuick.presetLayerMatches(" + H['item'] + r")\2", 1, regex=True)

    # 7. Reorder arrows find the preset on the current layer.
    mv = f"({H['item']}.{H['thickness']} == {DVT_THICK})):("
    s = edit(s, "reorder matches layer", mv,
             f"({H['item']}.{H['thickness']} == {DVT_THICK}) && floatQuick.presetLayerMatches({H['item']})):(", 2)

    # 8. Small "L2" badge on each preset button.
    badge_anchor = H["pointSize18"] + "\n\t\t\t\t\t\t}"
    s = edit(s, "layer badge", badge_anchor, badge_anchor + BADGE, 1)

    header = ("; floating.qmd + per-preset layers\n"
              "; Original: FouzR (https://github.com/FouzR/xovi-extensions), GPL-3.0\n"
              "; Patch: each pen preset remembers a layer; tapping it switches pen and layer.\n\n")
    open(dst, "w", encoding="utf-8").write(header + s)
    print(f"[ok] wrote {dst}")


if __name__ == "__main__":
    main()
