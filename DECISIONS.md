# Decision record

Brief 2.8, one point per section. Only the calls the brief left open; each links to its code and the PR with the full reasoning.

## 1. Data model

- **Meetings find their Issues and To-Dos by time window**, not stored links: whatever the team solved or created between start and end. The seeded meetings have no links, so one rule covers both. Tradeoff: later edits reach old summaries (see 5). ([meetings/service.py#L430-L447](server/app/modules/meetings/service.py#L430-L447), [#1](https://github.com/GoonerMAK/Level_10_Meeting/pull/1))
- **Issue source is a Measurable + week pair**, both or neither, week always a Monday ([issues.py#L25-L26](server/app/models/issues.py#L25-L26), [#L40-L43](server/app/models/issues.py#L40-L43)). A To-Do keeps its source Issue's id; deleting the Issue keeps the To-Do ([todos.py#L24](server/app/models/todos.py#L24)).
- **Nothing computed is stored.** Statuses, progress and rates come from plain functions ([calculations](server/app/calculations)) that the Team page, meeting summary and rules report share, so they can't disagree ([#3](https://github.com/GoonerMAK/Level_10_Meeting/pull/3)).
- **Two clocks:** "today" stays on `APP_NOW` while timestamps tick, so timers run and rows sort ([clock.py](server/app/core/clock.py), [#6](https://github.com/GoonerMAK/Level_10_Meeting/pull/6)). The clock pauses while the server is stopped instead of restarting at `APP_NOW`, which would send time backwards ([db/clock.py](server/app/db/clock.py), [#32](https://github.com/GoonerMAK/Level_10_Meeting/pull/32)).

## 2. API design

- **Another team's data is 404, not 403**, so a guessed id looks like a missing one ([permissions.py#L20-L22](server/app/core/permissions.py#L20-L22), [#2](https://github.com/GoonerMAK/Level_10_Meeting/pull/2)).
- **422 when the request is wrong, 409 when it clashes with current data**, e.g. solving a solved Issue. Every database rule has a plain message ([messages.py](server/app/core/messages.py), [#37](https://github.com/GoonerMAK/Level_10_Meeting/pull/37)).
- **Actions as named endpoints** in the brief's words (`/solve`, `/done`, `/undo`, `/next`, `/end`), not a generic status update, so each has its own rule and error.
- **Role checks in the services**, not the routes, so REST and the live connection share them ([#2](https://github.com/GoonerMAK/Level_10_Meeting/pull/2)).
- **Signed cookie, no session table; the web app forwards `/api`**, so no CORS and the WebSocket gets the cookie for free. Tradeoff: sign-out can't revoke a copied cookie ([#27](https://github.com/GoonerMAK/Level_10_Meeting/pull/27)).

## 3. Real-time, meeting state and recovery

- **WebSocket per open team page.** Meeting changes push the full state; list changes push only "changed" and the page refetches, so there's one way to load data ([README](README.md#live-connection), [#31](https://github.com/GoonerMAK/Level_10_Meeting/pull/31)).
- **Postgres owns the meeting.** A reconnect, refresh or late join gets the full state; opening the Meeting page joins, and joining twice is harmless ([#42](https://github.com/GoonerMAK/Level_10_Meeting/pull/42)).
- **No server ticks:** the state carries the section's end time and the server's now; each browser counts down from its gap to the server, so throttled tabs and wrong clocks agree.
- **Next names the section it leaves**, so a double click or an old tab can't skip one ([meetings/service.py#L140](server/app/modules/meetings/service.py#L140), [#30](https://github.com/GoonerMAK/Level_10_Meeting/pull/30)).
- **A meeting nobody has open for 30 minutes ends itself**, so a lost facilitator can't block the team. No takeover, as the brief rules out handoff ([#36](https://github.com/GoonerMAK/Level_10_Meeting/pull/36)).
- **Tradeoff:** connections live in memory ([hub.py](server/app/modules/live/hub.py)), so one server process.

## 4. Make it an Issue without duplicates

- **The database decides, not a lock:** a partial unique index allows one unsolved Issue per Measurable + week ([issues.py#L45-L51](server/app/models/issues.py#L45-L51)). There's no row to lock before the Issue exists.
- **Insert, and on conflict return the existing one:** 201 new, 200 existing, no error for the loser ([issues/service.py#L95](server/app/modules/issues/service.py#L95), [#26](https://github.com/GoonerMAK/Level_10_Meeting/pull/26)).
- **Solved mid-click:** retries up to 3 times, then 409 ([#L24](server/app/modules/issues/service.py#L24)).
- **Same pattern** keeps one running meeting per team ([meetings.py#L29](server/app/models/meetings.py#L29)). Proof: 10 clicks from 4 users make one Issue ([test_issues.py#L23](server/tests/test_issues.py#L23)).

## 5. Keeping past summaries unchanged (described, not built)

- **Today** the summary is worked out when read ([meetings/service.py#L373](server/app/modules/meetings/service.py#L373), [#33](https://github.com/GoonerMAK/Level_10_Meeting/pull/33)), so editing a score or reopening an Issue changes an old summary.
- **Plan:** at End, in the same transaction, save the finished summary as one fixed copy on the meeting, with a version number. Ended meetings read the copy; seeded meetings get theirs when seeded.
- **Tradeoff:** names and statuses stored twice, on purpose. Rejected: summary tables (more to keep in step) and replaying the audit trail (complex; seeded data has no history).

## Supporting 1,000 companies

- **Admins limited to their company:** today an Admin can open every team in every company ([permissions.py#L16-L17](server/app/core/permissions.py#L16-L17)); the To-Do owner list already checks it ([teams/service.py#L51](server/app/modules/teams/service.py#L51)). Add tests across two companies.
- **Live updates across server processes:** move connections and presence to Postgres LISTEN/NOTIFY or Redis.
- **Old meetings stay cheap** once summaries are saved copies (5).
