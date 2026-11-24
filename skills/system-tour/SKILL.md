---
name: system-tour
description: Build an animated, step-by-step "system tour" web page that shows how a solution's high-level design (HLD) behaves from several angles (normal use, scaling, failures, why each service exists) on one isometric map with moving request/response/event packets. Use when the user asks for an architecture tour, a system tour, an animated HLD, "show how the system behaves/works", "explain the architecture visually", an interactive flow of the services, or a page like system-tour.html.
---

# System tour

A system tour is one HTML page: an isometric map of the solution (people, entry points, services, stores, external systems) and a player that walks through **scenarios**. Each step lights only the nodes it uses and sends coloured packets along the wires: request, response, event, AI call, refused/blocked. A side panel explains the step in plain words and lists every move. Scenarios are grouped by **angle**, so the team sees how the solution behaves where it matters, not only what boxes exist.

The page opens on a **home view** where several areas of the system run at once on the same map, with the list of areas as a way into each scenario. A tour can be written in **several languages** (`meta.langs`, text as `{"en": …, "fr": …}`); the reader switches with the EN / FR control in the header.

The look, the animation and the interaction are fixed in `assets/engine.html`. **For a project you write only data** (one JSON file) and build it. Never re-create or hand-edit the engine inside a project; if the engine needs a change, change it in this skill so every tour gets it.

## Files

| File | What it is |
|---|---|
| `assets/engine.html` | The page: layout, styles, SVG drawing, animation, controls. Holds the `/*@@TOUR_DATA@@*/` marker. |
| `scripts/build.py` | Validates the tour JSON and writes the single-file HTML. `--check` validates only. |
| `references/data-format.md` | Every field of the JSON, the map grid and wire routing. Read before writing data. |
| `references/scenarios.md` | How to choose areas and angles, and how to write steps. Read before choosing scenarios. |
| `assets/example-tour.json` | A small, complete, synthetic tour that uses every feature. Copy its shape. |

## Workflow

1. **Read the HLD, not your memory.** Architecture docs (C4, diagrams), decision records, deployment files (compose, Helm, Terraform), API and event contracts, then code where the docs are thin. List: actors, entry points, identity, services, stores, bus, external systems, the trust boundary. Note for each one whether it is built, decided but not built, or still open.
2. **Choose the areas where the solution "turns"** and the angles for each (see `references/scenarios.md`). Show the user the short list of categories → scenarios (one line each) and wait for their OK, unless they already said what to cover.
3. **Write the tour JSON** in the project, next to its architecture docs (e.g. `docs/architecture/system-tour.json`). Lay the map out with the grid recipe in `references/data-format.md`.
4. **Build and validate** with the build script in this skill's own folder (the base directory Claude Code gives when it loads the skill; it depends on where the skill is installed, so never assume `~/.claude/skills`):
   ```bash
   python3 <skill-dir>/scripts/build.py docs/architecture/system-tour.json docs/architecture/system-tour.html
   ```
   Fix every ERROR. Read every warning and fix it or keep it on purpose (say which in your report).
5. **Test in a browser** (built-in browser pane; local files must sit inside the project folder to be interactive). Check:
   - no console errors;
   - every category and every scenario opens; step through each step at least once;
   - no label is covered and no wire crosses a box on a lit step (flip its `routes` entry if it does);
   - the home view: areas run and overlap, the panel's "Now running" and the lit rows follow them, clicking a row opens that scenario;
   - one scaling step (replicas and ×N badges), one failure step (DOWN badge), one "not chosen" step (HYPOTHETICAL stamp);
   - with several languages: switch language on the home view and on a step; every label, the legend and the side panel change;
   - keyboard: ← → steps, `,` `.` moves, space pause, `r` replay, 1–3 speed; the address updates to `#cat/scenario/step`;
   - phone width (375 px): no sideways scroll, the map zooms on the step's nodes.
   Take one screenshot as proof.
6. **Deliver:** the JSON is the source (commit it if the user asks), the HTML is the build. Offer to publish the HTML as an Artifact if it will be shared.

## Honesty rules (the tour must not oversell the design)

- Every node and every move traces back to something real in the HLD. Do not invent services, events or numbers.
- Anything not agreed or not built: `tc: true` on the node (dashed, "TO CONFIRM") and a `callout: ["tc", "To confirm", "…"]` on the step.
- An integration never called for real is "not verified", not "works".
- An option that was not chosen is shown only with `hypo: true` steps, under a "Why …" angle.
- Numbers (latency, counts, sizes) only when measured; say where they were measured ("measured locally").
- Client documents, real people and real data never appear; use roles and synthetic examples.

## Writing rules

- One idea per step. 1–2 short paragraphs in `body`; `<code>` for names of services, endpoints, events; `<b>` for the one word that matters.
- 3–10 moves per step (the validator warns above 12). Move labels under 40 characters, saying what travels ("save draft · signed context"), not the mechanism in full.
- Step `nav` is 1–2 words (it labels the step dots); `title` is a short sentence that states the point.
- Write in the language the user writes in, unless they ask otherwise; set `meta.lang`. For a bilingual tour set `meta.langs` and give every text a value per language; the validator lists what is still untranslated.
