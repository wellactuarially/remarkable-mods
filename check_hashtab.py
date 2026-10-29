#!/usr/bin/env python3
"""
Check a hashed .qmd against a tablet's qmldiff hashtab.

Every hash in a community .qmd was a real QML name on the firmware it was
written for. If a hash is missing from YOUR firmware's hashtab, that name no
longer exists (renamed, moved or removed), and the edit that uses it will
not apply. This is the quickest way to tell whether a 3.28 mod survives on 3.29.

Get the hashtab from the tablet (after running /home/root/xovi/rebuild_hashtable):
    scp root@<tablet-ip>:/home/root/xovi/exthome/qt-resource-rebuilder/hashtab .

Usage:
    python3 check_hashtab.py hashtab floating-layers.qmd [--unhash out.qml.txt]

--unhash writes a readable copy with every resolvable hash replaced by its name.
Format reference: asivery/qmldiff src/hashtab.rs (u64 BE hash, u32 BE length, bytes).
"""
import re
import struct
import sys

VERSION_KEY = 17607111715072197239  # hash of "!*HashTab-Version"


def load_hashtab(path):
    tab, version = {}, None
    with open(path, "rb") as f:
        data = f.read()
    i = 0
    while i + 12 <= len(data):
        h, n = struct.unpack(">QI", data[i:i + 12])
        s = data[i + 12:i + 12 + n].decode("utf-8", "replace")
        i += 12 + n
        if h == VERSION_KEY:
            version = s
        elif h != 0:
            tab[h] = s
    return tab, version


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    tab, version = load_hashtab(sys.argv[1])
    qmd_path = sys.argv[2]
    lines = open(qmd_path, encoding="utf-8").read().split("\n")
    print(f"hashtab: {len(tab)} names, QML environment version: {version}")

    missing = {}
    pat = re.compile(r'~&"?(\d+)&~|\[\[([\d.]+)\]\]')
    for ln, line in enumerate(lines, 1):
        if line.lstrip().startswith(";"):
            continue
        for m in pat.finditer(line):
            parts = [m.group(1)] if m.group(1) else m.group(2).split(".")
            for p in parts:
                if p and int(p) not in tab:
                    missing.setdefault(int(p), []).append(ln)

    if not missing:
        print("[ok] every hash resolves on this firmware.")
    else:
        print(f"[!] {len(missing)} hash(es) don't exist on this firmware:")
        for h, lns in sorted(missing.items(), key=lambda kv: kv[1][0]):
            print(f"  {h}  lines {lns[:8]}{' ...' if len(lns) > 8 else ''}")
            print(f"      first use: {lines[lns[0] - 1].strip()[:140]}")

    if "--unhash" in sys.argv:
        out = sys.argv[sys.argv.index("--unhash") + 1]

        def sub(m):
            if m.group(1):
                name = tab.get(int(m.group(1)))
                if name is None:
                    return m.group(0)
                return f'"{name}"' if m.group(0).startswith('~&"') else name
            names = [tab.get(int(p), p) for p in m.group(2).split(".")]
            return "[" + ".".join(names) + "]"

        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(pat.sub(sub, l) for l in lines))
        print(f"readable copy: {out}")

    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
