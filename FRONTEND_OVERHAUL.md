# Frontend Overhaul — Summary Document (Updated)

**Project:** Online Exam Monitoring & Integrity Analytics Platform
**Scope:** Frontend architecture, UI/UX, stakeholder accessibility, design consistency
**This revision:** re-audited against the latest repo state — significant new work
from the team since the last version of this document, several previously-flagged
issues are now fixed, two new issues found.

---

## 1. Design System

Shared visual language across the site — bold split panels, dark charcoal + coral
accent, confident typography. Original colors/copy, District/Zomato-inspired UX
patterns only.

### Tokens (defined in `static/css/login.css`, meant to be reused sitewide)

| Token | Value | Use |
|---|---|---|
| `--auth-ink` | `#14141c` | Dark panels, navbar, footer |
| `--auth-panel-2` | `#22222f` | Secondary tone for gradients |
| `--auth-accent` | `#ff5a36` | Primary actions, highlights, active states |
| `--auth-accent-dark` | `#e8461f` | Hover state |

### Shared components (`static/css/styles.css`, `login.css`)
`.btn`, `.btn-block`, `.primary-btn` / `.secondary-btn`, `.form-control`, `.card`,
`.sr-only`

### Rules for every page
1. Extend `base.html`; include `login.css` for the shared tokens
2. Reuse existing classes — don't invent new button/card/color styles
3. No hardcoded data, ever — every number/title/status comes from the real backend
4. No `alert()` / `confirm()` — inline messages or modals (pattern: `exam_window.html`)
5. Status/risk indicators need a text label, never color alone
6. Test on mobile (<768px) before calling a page done

---

## 2. Test Suite Health

**296 tests, 2 failing** (up from 145 at the last check — the team has added
substantial new coverage). Both failures share one root cause:

```
sqlite3.OperationalError: no such table: Candidates
  at modules/face_verification.py -> _get_registered_photo_path()
```

`modules/face_verification.py` resolves its own database connection independently
instead of sharing the app's DB path, so it isn't pointed at the test database when
tests run. **This is the same class of bug** flagged in the invigilator-dashboard
review (`modules/analytics.py`, `modules/flags_storage.py`) and hit directly during
the exam-window work (`routes/pages.py` originally had the same issue, fixed by
reusing `routes.auth.get_db_connection()`).

**Recommendation:** this needs an owner. Every module that talks to SQLite should
go through one shared connection helper (`routes.auth.get_db_connection()` or
equivalent), not redeclare its own `DATABASE` path. Left unfixed, this will keep
resurfacing as a test failure every time a new module is added.

Failing tests:
- `tests/test_alert_evidence.py::test_get_alert_evidence_allows_invigilator_and_returns_evidence`
- `tests/test_integration_full_flow.py::test_full_candidate_journey_end_to_end`

---

## 3. Previously Flagged Issues — Now Fixed

### 3.1 Environment check page
Was: all 6 checks (`setTimeout`-simulated, always "Ready" regardless of real
hardware). **Now:** real `getUserMedia`/`navigator.onLine` calls, "Start
Examination" is genuinely gated on checks passing, and it now takes and forwards a
real `exam_id` into `/start_exam/<id>` instead of being a dead end. Good fix — matches
the brief's requirement exactly.

### 3.2 Exams listing page
Was: hardcoded card content, and every card's "Start Exam" link pointed to
`exam_id=1` regardless of which exam it was — a real bug where clicking any exam
always started the same one. **Now:** `routes/pages.py` queries the real `Exams`
table (with a `LEFT JOIN` for live question counts) and `exams.html` loops over
real rows. Correctly reuses `get_db_connection()`, so it didn't reintroduce the
DB-path bug. Confirmed fixed.

### 3.3 Results / Report / Analytics pages
Checked for hardcoded values and placeholder content per the original brief
(sections 16–17). All three (`results.js`, `report.js`, `analytics.js`) fetch real
data — no dummy arrays, no "coming soon" text, no TODO markers. `report.html` is a
real 112-line implementation, not a placeholder.

---

## 4. New Findings

### 4.1 Results & Analytics pages — still on the old blue palette
`static/css/results.css` and `static/css/analytics.css` were never retinted to the
coral/dark design system — they still use the pre-redesign blue
(`#2563eb`, `#1e3a8a`, `#1e40af`) throughout headers, icons, and gradient cards.
Every other page audited in this pass (`login`, `register`, `home`,
`invigilator_dashboard`, `exam_window`, and the newer `candidate_status`,
`evidence_viewer`, `support_tickets`, `violations_log`) correctly extends
`base.html` + includes `login.css` and uses the shared tokens. These two are the
remaining outliers — worth a retint pass so the whole site is visually one product.

### 4.2 `webcam.js` still uses a browser `alert()`
One instance: camera-permission failure shows `alert("Could not access webcam...")`
instead of inline UI. Low severity (it's a genuine error case), but inconsistent
with the "no alert()/confirm()" rule applied everywhere else, including the same
kind of camera-permission failure in `exam_window.js`, which handles it with an
inline warning banner instead.

---

## 5. Work Completed This Pass (from earlier in the project)

Full detail preserved from the previous version of this document — condensed here:

- **Login/Register:** mock `alert()`-based auth replaced with real `/login` and
  `/register` calls; consolidated webcam implementation; split-panel redesign;
  fixed a `base.html` navbar bug that broke the public nav on auth pages.
- **Homepage:** full redesign — hero, portal discovery (Candidate/Invigilator, no
  fake Admin portal), feature cards, how-it-works, footer nav.
- **Header/footer nav:** fixed a real bug where invigilators got the candidate
  navbar (broken links to session-gated candidate routes); added active states,
  mobile hamburger menu, invigilator-specific nav branch.
- **Invigilator dashboard:** audited (already real, backend-driven, well-built by
  the team) and given an accessibility pass — ARIA labels on charts, table
  captions/scopes, live-region updates, a non-color-only risk-cluster legend.
- **Exam window:** real exam title/duration (was hardcoded), monitoring status bar
  wired to a real camera/mic stream, submit-confirmation modal, palette with
  answered/current/unanswered states (icon + color, not color alone), removed
  `alert()`/`confirm()`. Two post-merge bugs from real testing were also fixed:
  unmuted monitoring video causing mic feedback, and Submit staying clickable on
  a zero-question exam.

---

## 6. Outstanding / Open Items

| Item | Status |
|---|---|
| `results.css` / `analytics.css` still blue, not coral-system | **Open — new finding** |
| `webcam.js` alert() on camera failure | **Open — minor, new finding** |
| Shared DB-connection helper adoption across all modules | **Open — recurring, needs an owner** (2 real test failures right now) |
| `answer_review`, `candidate_status`, `evidence_viewer`, `support_tickets`, `violations_log` | Correctly follow the design system; not deep-audited for hardcoded data in this pass — worth a follow-up sweep |

---

## 7. For the Team

1. **Read `login.css` and `styles.css` first.** Reuse tokens/components.
2. **No hardcoded data, ever.**
3. **No `alert()`/`confirm()`.** Copy the modal pattern in `exam_window.html`.
4. **Status/risk indicators need a text label**, not color alone.
5. **Test on mobile** (<768px).
6. **Run `python -m pytest -q` before opening a PR** — currently 2 known failures
   (section 2), unrelated to most frontend changes, but check you haven't added a
   third by giving a new module its own DB path.
7. Check in before inventing a new color or component.
