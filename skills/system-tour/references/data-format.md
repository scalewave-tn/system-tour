# Tour data format

One JSON object. `build.py` checks all of this; this page says what each field means and how to lay out the map.

```json
{
  "meta":   {"title": "…", "crumb": "…", "heading": "…", "lang": "en", "mapLabel": "…"},
  "zone":   {"from": [0.3, -7.6], "to": [18.4, 11.4], "label": "Acme · private cloud"},
  "routes": {"api|web": "uv"},
  "home":   {"title": "…", "intro": ["…"], "play": ["use/order"]},
  "icons":  {"rocket": "M12 2l4 8h-8z"},
  "nodes":  [ … ],
  "categories": [ … ]
}
```

## meta

| Field | Use |
|---|---|
| `title` (required) | Browser tab title. 2–4 words: "Acme Orders Tour". |
| `crumb` | Small line above the heading: "<system name> · architecture tour". |
| `heading` | Big heading: "How <system> behaves". |
| `lang` | `html lang`, e.g. `en`, `fr`, `ar`. |
| `mapLabel` | Accessible label of the map. |
| `langs` | Languages the tour is written in, first one is the default: `["en", "fr"]`. Two or more show an EN / FR switcher in the header. See **Languages**. |
| `ui` | Optional overrides of the page's own words, per language: `{"fr": {"next": "Suite"}}`. Keys are in `UI_TEXT` in `engine.html`; English and French are built in. |

## nodes

```json
{"id": "orders", "kind": "service", "u": 9, "v": 0, "label": "orders", "sub": "Spring Boot", "icon": "cart", "name": "Orders", "tc": false, "small": false}
```

| Field | Use |
|---|---|
| `id` | Short word used by flows. |
| `kind` | `people` (crowd on a platform), `entry` (front door, web, gateway, BFF), `identity` (IdP), `service`, `ai`, `bpm` (workflow engine), `store` (cylinder: DB, bus, cache, index, file store), `ext` (dashed box: system you do not run). Kind sets shape and colour. |
| `u`, `v` | Grid position (see layout). Decimals are fine. |
| `label` | Text on or beside the node. ≤ 16 characters for boxes. |
| `sub` | Small second line (technology, role). |
| `icon` | Box icon: `globe door key letter flow file bell shield spark search chat user cart card box gear lock cloud queue chart clock phone api`, or one you add in `icons` (24×24 SVG path, stroked). |
| `name` | Name used in the side panel and caption when it differs from `label`. |
| `tc` | true = not agreed or not built: dashed outline, "TO CONFIRM" badge, dashed wires. `ext` boxes are always drawn dashed (outside your control); they get the badge only with `tc: true`. |
| `small` | `people` only: smaller platform (for a secondary actor). |

## Layout: the isometric grid

Screen position: `x = (u − v) × 30`, `y = (u + v) × 15`.
- To move a node **right**: +u and −v. **Down**: +u and +v. **Up**: −u and −v. **Left**: −u and +v.
- Keep at least 3 grid units between boxes on both axes (the validator warns under 2.5).

A recipe that reads left → right like a request:

| Column | Typical u, v |
|---|---|
| People | (−1, 9); a secondary actor `small` at the top right (12, −14) |
| Entry (web, gateway/BFF) | (2, 6), (5, 3) |
| Identity | (2, 0.5) |
| Services, 2 columns × up to 4 rows | u ∈ {9, 12}, v ∈ {−3, 0, 3, 6} |
| Stores (DB, bus, cache) | u = 16, v ∈ {−4.5, −1, 2.5, 6}; an index under the services at (8.5, 10) |
| External systems along the top | v ≈ −9, u from 5 to 18 |
| Outside model/API on the right | (20, 7) |
| `zone` around what you run | from (0.3, −7.6) to (18.4, 11.4) |

Put services that talk a lot next to each other, and the bus and DB close to the services that use them most. Re-check after building: the grid recipe is a start, the screenshot decides.

## routes

Each wire is an L: it walks one axis, turns once, then walks the other. By default (`uv`) it leaves the alphabetically first id along `u`, turns, then goes along `v`. When a wire crosses a box or runs over another wire, flip it:

```json
"routes": {"gateway|orders": "uv", "bus|orders": "vu"}
```

The key is the two ids **sorted alphabetically**, joined by `|`. `uv` = from the first id walk along u first (the default), `vu` = walk along v first. Replicas (`orders#1`) share the wire of their node.

## categories → scenarios → steps

```json
{"id": "use", "name": "Using the app", "scen": [
  {"id": "order", "name": "Place an order", "summary": "One line on what this scenario shows.", "steps": [ … ]}
]}
```

`id`s are lowercase slugs; they make the address `#use/order/2`.

### step

| Field | Use |
|---|---|
| `nav` (required) | 1–2 words under the step dot. |
| `title` (required) | The point of the step, one short sentence. |
| `body` (required) | List of paragraphs (HTML allowed: `<code>`, `<b>`). |
| `flows` (required) | The moves, in order (below). |
| `callout` | `["tc", "To confirm", "text"]`, `["tip", "Why it matters", "text"]` or `["bad", "Risk", "text"]`. |
| `facts` | List of short takeaways, shown as bullets. Good for a closing step. |
| `extra` | Node ids to light although no move touches them (e.g. alternatives under discussion). |
| `scale` | `{"orders": 3}`: draw 3 instances of `orders` on this step (×3 badge). Needed before a flow can use `orders#2`. |
| `down` | `["payments"]`: grey the node, cross it, show a red DOWN badge. |
| `hypo` | true = an option that was not chosen: ⚠ before the title and a "HYPOTHETICAL · OPTION NOT CHOSEN" stamp. |

### flows (moves)

```json
["from", "to", "type", "label", {"with": true}]
```

| Part | Values |
|---|---|
| `from`, `to` | Node ids; `id#n` targets replica n (0-based) when the step has `scale`. |
| `type` | `req` request (orange), `res` response (green), `evt` event on the bus (violet), `ai` call to a model (yellow), `err` refused/failed (red). |
| `label` | What travels, < 40 chars. Optional; omit it for a plain hop. |
| `with` | Start together with the previous move (fan-out, parallel). |
| `block` | Stop at 80 % of the way and blink red: never reaches the target (target down, refused). |
| `park` | Arrive and wait beside the target (a message held in a queue until a consumer returns). |

Moves play one after the other, 350 ms apart, each lasting with its wire length. A step loops until the user moves on.

## Languages

Every piece of text a reader sees may be plain text or one entry per language:

```json
"title": {"en": "The proxy holds the key", "fr": "Le proxy garde la clé"}
```

This works for `meta` title/crumb/heading/mapLabel, `zone.label`, node `label`/`sub`/`name`, category `name`, scenario `name`/`summary`, step `nav`/`title`, each `body` paragraph, each `facts` item, callout title and text, move labels, and `home` title/intro. Ids, node kinds and code names stay as they are.

- Plain text is shown in every language; keep it for names that do not translate (`Postgres`, `/validate`, `SSE`).
- With two or more `langs`, the validator warns when a step title, body, fact, callout, nav, scenario or category name is still plain, and when a language is missing from an entry (that entry falls back to the first language).
- The reader's choice is kept in the browser (`localStorage`) and the page's `lang` follows it.
- Translated node labels must still fit their box (≤ 16 characters for cubes).

## home

The home view is the page's landing: the whole map, with several areas of the system running at once (each next area starts halfway through the previous one). Running areas are lit and the rest is softened; the side panel says what is running and lists every category and scenario with its `summary`, as a way in. `#home` is its address; a step address still opens that step.

| Field | Use |
|---|---|
| `title` | Heading of the home panel. Default "The system at work". |
| `intro` | Paragraphs above the list of areas: what the reader is looking at. |
| `play` | What runs: `"cat/scenario"` (all its steps) or `"cat/scenario/step"` (1-based), in order. Default: every step of the **first** category that has no `hypo`, `down` or `scale`. `false` turns the home view off. |

Pick normal-use steps for `play`. Failures and rejected options read as noise when several run at once; they belong to their own scenarios.
