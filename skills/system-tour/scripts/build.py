#!/usr/bin/env python3
"""Validate a system-tour JSON file and build the single-file HTML tour.

usage: build.py TOUR.json OUT.html     validate, then write the page
       build.py TOUR.json --check      validate only

Errors stop the build (exit 1). Warnings are printed and the build goes on.
"""
import json
import re
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "assets" / "engine.html"
MARK = "/*@@TOUR_DATA@@*/null"

KINDS = {"people", "entry", "identity", "service", "ai", "bpm", "store", "ext"}
CUBES = {"entry", "identity", "service", "ai", "bpm"}
TYPES = {"req", "res", "evt", "ai", "err"}
OPTS = {"with", "block", "park"}
CALLOUTS = {"tip", "tc", "bad"}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, out = Path(argv[1]), argv[2]
    try:
        tour = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR {src}: not valid JSON: {e}")
        return 1
    engine = ENGINE.read_text(encoding="utf-8")
    errors, warnings = validate(tour, engine)
    for w in warnings:
        print("warn ", w)
    for e in errors:
        print("ERROR", e)
    stats = summary(tour)
    if errors:
        print(f"{len(errors)} error(s), {len(warnings)} warning(s). Nothing written.")
        return 1
    print(f"ok: {stats}; {len(warnings)} warning(s)")
    if out == "--check":
        return 0
    data = json.dumps(tour, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    Path(out).write_text(engine.replace(MARK, data), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def summary(t):
    cats = t.get("categories") or []
    scen = [s for c in cats for s in c.get("scen", [])]
    steps = [st for s in scen for st in s.get("steps", [])]
    flows = sum(len(st.get("flows", [])) for st in steps)
    return f"{len(t.get('nodes') or [])} nodes, {len(cats)} categories, {len(scen)} scenarios, {len(steps)} steps, {flows} flows"


def validate(t, engine):
    E, W = [], []
    icons = set(re.findall(r"^\s+([a-z]+):'M", engine, re.M)) | set((t.get("icons") or {}).keys())

    meta = t.get("meta") if isinstance(t.get("meta"), dict) else {}
    langs = meta.get("langs")
    if langs is not None and (not isinstance(langs, list) or not langs or not all(isinstance(x, str) and x for x in langs)):
        E.append("meta.langs must be a non-empty list of language codes, e.g. [\"en\", \"fr\"]")
        langs = None
    langs = langs or [meta.get("lang") or "en"]
    multi = len(langs) > 1

    def tx(x, where, required=False, translate=False):
        """Text is plain or {lang: text}. Returns every variant (for length checks)."""
        if x is None or x == "":
            if required:
                E.append(f"{where} is required")
            return []
        if isinstance(x, str):
            if translate and multi:
                W.append(f"{where}: plain text in a {'/'.join(langs)} tour; give it one entry per language")
            return [x]
        if isinstance(x, dict):
            extra = set(x) - set(langs)
            if extra:
                E.append(f"{where}: unknown language(s) {sorted(extra)}; meta.langs is {langs}")
            missing = [l for l in langs if not x.get(l)]
            if missing:
                W.append(f"{where}: missing {', '.join(missing)} (falls back to {langs[0]})")
            bad = [k for k, v in x.items() if not isinstance(v, str)]
            if bad:
                E.append(f"{where}: values must be text")
            return [v for v in x.values() if isinstance(v, str)]
        E.append(f"{where}: must be text or {{lang: text}}")
        return []

    if not tx(meta.get("title"), "meta.title", required=True):
        pass
    for k in ("crumb", "heading", "mapLabel"):
        tx(meta.get(k), f"meta.{k}")
    ui = meta.get("ui")
    if ui is not None and not (isinstance(ui, dict) and all(isinstance(v, dict) for v in ui.values())):
        E.append("meta.ui must be {lang: {key: text}}")

    nodes = t.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        E.append("nodes: a non-empty list is required")
        return E, W
    ids = {}
    for i, n in enumerate(nodes):
        where = f"nodes[{i}]"
        nid = n.get("id")
        if not isinstance(nid, str) or not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", nid):
            E.append(f"{where}: id must be a word (letters, digits, _ or -), got {nid!r}")
            continue
        if nid in ids:
            E.append(f"{where}: duplicate id {nid!r}")
        ids[nid] = n
        if n.get("kind") not in KINDS:
            E.append(f"node {nid}: kind must be one of {sorted(KINDS)}")
        for k in ("u", "v"):
            if not isinstance(n.get(k), (int, float)):
                E.append(f"node {nid}: {k} must be a number")
        labels = tx(n.get("label"), f"node {nid}: label", required=True)
        tx(n.get("sub"), f"node {nid}: sub")
        tx(n.get("name"), f"node {nid}: name")
        if n.get("icon") and n["icon"] not in icons:
            E.append(f"node {nid}: unknown icon {n['icon']!r} (known: {', '.join(sorted(icons))})")
        for lab in labels:
            if n.get("kind") in CUBES and len(lab) > 16:
                W.append(f"node {nid}: label {lab!r} is long; it may run into a neighbour")

    placed = [n for n in nodes if isinstance(n.get("u"), (int, float)) and isinstance(n.get("v"), (int, float))]
    for i, a in enumerate(placed):
        for b in placed[i + 1:]:
            du, dv = abs(a["u"] - b["u"]), abs(a["v"] - b["v"])
            if du < 0.01 and dv < 0.01:
                E.append(f"nodes {a['id']} and {b['id']} sit on the same spot")
            elif du < 2.5 and dv < 2.5:
                W.append(f"nodes {a['id']} and {b['id']} are close ({du:g}, {dv:g} apart); keep 3 grid units between boxes")

    for key, mode in (t.get("routes") or {}).items():
        parts = key.split("|")
        if len(parts) != 2 or any(p not in ids for p in parts):
            E.append(f"routes[{key!r}]: must be 'a|b' with two node ids")
        elif parts != sorted(parts):
            E.append(f"routes[{key!r}]: ids must be in sorted order: {'|'.join(sorted(parts))!r}")
        if mode not in ("uv", "vu"):
            E.append(f"routes[{key!r}]: value must be 'uv' or 'vu'")

    z = t.get("zone")
    if z is not None:
        ok = isinstance(z, dict) and all(isinstance(z.get(k), list) and len(z[k]) == 2 for k in ("from", "to"))
        if not ok:
            E.append("zone: needs from:[u,v] and to:[u,v]")
        else:
            tx(z.get("label"), "zone.label")

    cats = t.get("categories")
    if not isinstance(cats, list) or not cats:
        E.append("categories: a non-empty list is required")
        return E, W

    used = set()
    seen_cat = set()
    for c in cats:
        cid = c.get("id")
        if not isinstance(cid, str) or not SLUG.match(cid) or cid in seen_cat:
            E.append(f"category {cid!r}: id must be a unique lowercase slug")
        seen_cat.add(cid)
        tx(c.get("name"), f"category {cid}: name", required=True, translate=True)
        scens = c.get("scen") or []
        if not scens:
            E.append(f"category {cid}: scen must list at least one scenario")
        seen_scen = set()
        for s in scens:
            sid = s.get("id")
            here = f"{cid}/{sid}"
            if not isinstance(sid, str) or not SLUG.match(sid) or sid in seen_scen:
                E.append(f"scenario {here}: id must be a lowercase slug, unique in its category")
            seen_scen.add(sid)
            tx(s.get("name"), f"scenario {here}: name", required=True, translate=True)
            tx(s.get("summary"), f"scenario {here}: summary", translate=True)
            steps = s.get("steps") or []
            if not steps:
                E.append(f"scenario {here}: needs at least one step")
            for j, st in enumerate(steps, 1):
                at = f"{here}/{j}"
                tx(st.get("nav"), f"step {at}: nav", required=True, translate=True)
                tx(st.get("title"), f"step {at}: title", required=True, translate=True)
                if not isinstance(st.get("body"), list) or not st["body"]:
                    E.append(f"step {at}: body must be a list of paragraphs")
                else:
                    for q, para in enumerate(st["body"], 1):
                        tx(para, f"step {at}: body[{q}]", required=True, translate=True)
                if st.get("facts") is not None:
                    if not isinstance(st["facts"], list):
                        E.append(f"step {at}: facts must be a list")
                    else:
                        for q, fact in enumerate(st["facts"], 1):
                            tx(fact, f"step {at}: facts[{q}]", required=True, translate=True)
                scale = st.get("scale") or {}
                for nid, k in scale.items():
                    if nid not in ids:
                        E.append(f"step {at}: scale names unknown node {nid!r}")
                    elif not isinstance(k, int) or k < 2:
                        E.append(f"step {at}: scale[{nid}] must be an integer >= 2")
                    else:
                        used.add(nid)
                for key in ("down", "extra"):
                    for nid in st.get(key) or []:
                        if nid not in ids:
                            E.append(f"step {at}: {key} names unknown node {nid!r}")
                        else:
                            used.add(nid)
                co = st.get("callout")
                if co is not None and (not isinstance(co, list) or len(co) != 3 or co[0] not in CALLOUTS):
                    E.append(f"step {at}: callout must be [type, title, text] with type in {sorted(CALLOUTS)}")
                elif co is not None:
                    tx(co[1], f"step {at}: callout title", required=True, translate=True)
                    tx(co[2], f"step {at}: callout text", required=True, translate=True)
                flows = st.get("flows")
                if not isinstance(flows, list) or not flows:
                    E.append(f"step {at}: flows must list at least one move")
                    continue
                if len(flows) > 12:
                    W.append(f"step {at}: {len(flows)} moves; more than 12 is hard to follow, split the step")
                for m, f in enumerate(flows, 1):
                    fw = f"step {at} move {m}"
                    if not isinstance(f, list) or not 3 <= len(f) <= 5:
                        E.append(f"{fw}: must be [from, to, type, label?, opts?]")
                        continue
                    for end in f[:2]:
                        if not isinstance(end, str):
                            E.append(f"{fw}: {end!r} is not a node id")
                            continue
                        base, _, idx = end.partition("#")
                        if base not in ids:
                            E.append(f"{fw}: unknown node {base!r}")
                            continue
                        used.add(base)
                        if idx:
                            if not idx.isdigit():
                                E.append(f"{fw}: replica in {end!r} must be a number")
                            elif int(idx) >= scale.get(base, 1):
                                E.append(f"{fw}: {end!r} needs scale {{{base}: {int(idx) + 1}}} or more on this step")
                    if f[0] == f[1]:
                        E.append(f"{fw}: from and to are the same")
                    if f[2] not in TYPES:
                        E.append(f"{fw}: type must be one of {sorted(TYPES)}")
                    for lab in (tx(f[3], f"{fw}: label") if len(f) >= 4 else []):
                        if len(lab) > 42:
                            W.append(f"{fw}: label is {len(lab)} chars; keep it under 40")
                    if len(f) == 5:
                        o = f[4]
                        if not isinstance(o, dict) or set(o) - OPTS:
                            E.append(f"{fw}: opts may only hold {sorted(OPTS)}")
                    if m == 1 and len(f) == 5 and isinstance(f[4], dict) and f[4].get("with"):
                        W.append(f"{fw}: 'with' on the first move has nothing to start with")

    home = t.get("home")
    if home is not None:
        if not isinstance(home, dict):
            E.append("home must be an object")
        else:
            tx(home.get("title"), "home.title", translate=True)
            intro = home.get("intro")
            for q, para in enumerate(intro if isinstance(intro, list) else ([] if intro is None else [intro]), 1):
                tx(para, f"home.intro[{q}]", translate=True)
            play = home.get("play")
            if play is not None and play is not False:
                if not isinstance(play, list) or not play:
                    E.append("home.play must be a list of 'cat/scenario' or 'cat/scenario/step', or false")
                else:
                    for ref in play:
                        parts = str(ref).split("/")
                        c = next((c for c in cats if c.get("id") == parts[0]), None)
                        s = c and len(parts) > 1 and next((s for s in c.get("scen", []) if s.get("id") == parts[1]), None)
                        ok = bool(s) and len(parts) in (2, 3)
                        if ok and len(parts) == 3:
                            ok = parts[2].isdigit() and 1 <= int(parts[2]) <= len(s.get("steps", []))
                        if not ok:
                            E.append(f"home.play: {ref!r} does not name a scenario or step")

    for nid in ids:
        if nid not in used:
            W.append(f"node {nid} is never used by any step; drop it or give it a scenario")
    return E, W


if __name__ == "__main__":
    sys.exit(main(sys.argv))
