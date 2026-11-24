# Choosing scenarios

The tour exists so a team understands how the solution behaves in the few areas where the design "turns": the places where a decision shapes what happens. A tour that animates every endpoint teaches nothing. Pick the areas first, then look at each from the angles that apply.

## 1. Find the areas where the solution turns

Look in the HLD for the decisions with consequences. Typical ones:

- **The front door and identity**: how a user gets a session, where tokens live, what the browser holds.
- **The main business journeys**: the 2–4 things users do most (create, approve, send, pay, search).
- **Asynchronous work**: the bus, the outbox, what is an event and what is a call, who waits for whom.
- **Data ownership**: which service owns which data; how another service reads it (call, projection, event).
- **Access control**: where rights are checked, how a change of rights reaches every instance.
- **AI or other probabilistic parts**: what they may decide, what a person confirms.
- **Search, reporting, files**: separate stores that are fed and can lag.
- **Integrations**: outside systems, and which of them are agreed, built or verified.

## 2. Look at each area from the angles that apply

The default categories (rename them in the user's language, drop one if empty, add one the project needs):

| Category | Question it answers | Scenario shape |
|---|---|---|
| **Using the app** | What happens, service by service, when someone does a real task? | One scenario per journey, 2–4 steps, the request from person to stores and back, with the events it starts. |
| **Scaling** | Does it still hold with several instances and more load? | `scale` on the services; show any instance serving any request, shared state, one-time ids refused on every instance, a single relay or leader, a part that scales on its own. |
| **When something fails** | What keeps working when one part is down, and what stops? | One scenario per dependency that can fail: `down` on it; `block` on the moves that fail; `park` on events waiting in a durable queue; a second step "back up" where they drain. End with what the user sees. |
| **Why a service** | Why is it split this way rather than another way? | First steps `hypo: true` showing the option not chosen and its problem; then the chosen design; a closing step with `facts`. |

Other angles that some projects need: **Security** (what an attacker with X can and cannot do), **Data residency / privacy** (where each piece of data goes), **Deployment / release** (how a new version rolls out), **Onboarding** (a new tenant, a new organisation).

Aim for 3–6 scenarios per category and 2–4 steps per scenario. A first version with 8–12 scenarios is better than a complete one nobody finishes.

## 3. Write each step

- The `title` states the point in one sentence: "Writes succeed; events leave when the bus is back."
- The `body` says what happens and why it matters, in plain words a non-developer can follow. Name services and events in `<code>`.
- The moves show the mechanism; do not repeat every move in the text.
- When something is not settled, say it in a `callout` of type `tc`, and mark the node `tc`.
- A failure scenario ends with what the user sees ("only the search page shows 'search unavailable'").
- A "why" scenario ends with 2–4 `facts`, the takeaways.
