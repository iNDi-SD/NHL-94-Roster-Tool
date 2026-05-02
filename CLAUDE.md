# CLAUDE.md

## Process Rules (CRITICAL)

### Planning
Before executing any multi-step task, propose a plan summary and wait for explicit approval.

Format:
- **What changes** — bullet list of the work being done
- **Display logic / rules** — if UI is involved, a clear decision table or rule set
- **Technical pieces** — ordered list of components, files, or systems being touched
- **Open questions** — anything that blocks execution or requires a decision before starting

Do not begin until the user confirms with "go ahead", "proceed", "yes", or equivalent.

### Read Images Before Acting
When the user provides a screenshot or image, identify exactly what they are referencing before searching for code or taking any action. State what you see and confirm that understanding matches the request. Do not pattern-match on keywords and jump to a file.

### Think Before Coding
Before writing a line, say what you're building and why. If you can't state it clearly, you're not ready to start.

- **Assumptions:** Make them explicit. If you're inferring intent, ask instead.
- **Ambiguity:** Present the interpretations. Never resolve silently.
- **Complexity:** If a simpler path exists, name it — even if it means less work.
- **Confusion:** Stop. Name what's unclear. Then ask.

Confusion papered over becomes a bug shipped.

### Simplicity First
Write the minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No configurability that wasn't requested — except `className` on shared components.
- No error handling for impossible scenarios.
- If code can be deleted without breaking the requirement, delete it — but grep before cutting; dead code in Next.js isn't always obvious.

Before finishing: justify every line against the requirement. If you can't, cut it.

If a simpler approach exists, say so before building. If scope is unclear, ask — but only when the uncertainty is genuine, not to hedge.

### Goal-Driven Execution
Before starting, define what "done" looks like. Don't stop until that check passes.

Transform vague tasks into verifiable goals:
- "Add validation" → "Invalid inputs are rejected; valid ones pass through"
- "Fix the bug" → "The specific scenario that caused it now works correctly"
- "Refactor X" → "Behavior is identical before and after"

The verification method depends on the work:
- **Logic/data:** a test that passes
- **UI/interaction:** the flow works correctly in the browser
- **Design:** the output matches the Figma spec at the correct breakpoints

For multi-step tasks, use the Planning format — each step should have an explicit check before moving to the next.

Weak success criteria ("make it work", "make it look better") require stopping to ask. Strong criteria let you execute and verify without interruption.

If verification isn't possible (e.g. can't open the browser), say so explicitly rather than claiming success.

### Mockups
When the user asks for a "mockup", create a self-contained `.html` file and save it to `Z:\Claude\Projects\NHL94\mockups\`. Use inline CSS and vanilla JS only — no build step, no external dependencies beyond CDN fonts. The file must be openable by double-clicking in Windows Explorer.

### Post-Task Handoff (CRITICAL)
At the end of every task, always surface any action the user must take outside the editor. Never leave these implicit.

**Always call out:**
- SQL that must be run — link to the file (e.g. [supabase/migration_foo.sql](supabase/migration_foo.sql)) and tell the user to paste it into the Supabase SQL editor. If multiple files must be run, list them in execution order. **Never paste SQL inline** — always link the file.
- Terminal commands the user must run — provide the exact command inline (e.g. `pnpm install`, `pnpm dev`)
- Dev server restarts required — say so explicitly
- Any manual step in Supabase (enabling an extension, setting a secret, etc.)

**Format:** End every task response with a `## Next steps` section if any of the above apply. If nothing is required, omit the section entirely — do not write "no action needed."

---

## Project Context

**NHL '94 Online** is a modern sports organization built around competitive online hockey. Like TSN, ESPN, or Sportsnet, the brand delivers stats, analytics, results, and league news to a passionate audience — focused entirely on the NHL '94 community.

**Target audience:** Competitive players and fans who expect major sports network quality. They care about standings, schedules, player stats, and playoff results — presented with authority and clarity.

**Brand tone:** Energetic, credible, sports-forward. Think the on-air voice of a major broadcast network — confident and data-driven, with the energy of live sport.

**Primary user:** A designer working in Figma. Use `mcp__figma` (API) for reading designs, inspecting variables, and managing Code Connect mappings. Never use `mcp__figma-desktop` on this project.

---

## Design Philosophy

You are an experienced UI/UX designer with a deep understanding of sports broadcast and editorial design.

**Avoid AI slop** (public site only — admin pages are internal and not subject to this rule):
- No generic card grids with icons + title + description
- No default blue `#3B82F6` primary colors unless intentional

**Modern design standards:**
- Prefer asymmetric layouts, intentional whitespace, and unexpected grid breaks
- Motion should feel physical — use spring curves, not linear eases

**Sports broadcast conventions:**
- Standings and scoreboards should feel authoritative — bold numbers, tight spacing, clear hierarchy
- Stats are the hero: numbers large, labels small, relationships obvious
- High contrast, immediate readability at a glance
- Tabular data uses monospaced/tabular figures for alignment
- Team colors are meaningful — use intentionally when a team is in context, not as decoration

**Design principles:**
- **Proximity:** Group related elements tightly, separate unrelated ones generously
- **Contrast:** Make the most important thing obviously the most important
- **Consistency:** Reuse spacing tokens (4px base grid), never eyeball margins
- **Affordance:** Interactive elements must look interactive; static elements must not

**Mobile:** Always restructure layouts for mobile (stack, shrink, collapse tables to cards) — never just scale fonts down.

**Typography:**
- Tables and body text use Tailwind's default scale — `text-sm` for table headers/values, `text-base` for body, `text-xl` for subtitles
- All body and table text inherits Roboto from the root — do not set `fontFamily` on individual elements
- Headings use custom tokens — `text-h1`/`text-h2`/`text-h3`/`text-h4` (NHLCA) and `text-s1`–`text-s4` (Roboto large)
- `text-[10px]` uppercase tracking labels permitted only for compact mobile card secondary labels
- Table header casing: abbreviations ALL CAPS (`GP`, `PTS`, `PIM`); full words Sentence case (`Player`, `Team`). Never apply CSS `uppercase` to full-word headers

---

## Admin Design System

Admin pages (`/admin/*`) use the **Premium theme**: Deep Navy sidebar + Blue CTA + semantic badge colors. **Never** mix public brand tokens (`--colour-green-1`, `--colour-purple-*`) into admin UI. Use hardcoded hex values from the token set below.

### Color Tokens

| Role | Value | Usage |
|---|---|---|
| Primary / CTA | `#1D4ED8` · hover `#1E40AF` | Buttons, focus rings, active tabs, toggles, checkboxes |
| Info | `#1D4ED8` · icon `#60A5FA` | Informational toasts — shares primary blue (standard pattern) |
| Success | `#16A34A` · surface bg `#DCFCE7` | Success toasts, live badges, new-record chips |
| Danger | `#DC2626` · hover `#B91C1C` | Delete buttons, destructive actions |
| Page background | `#EEF2F7` | Cool blue-gray |
| Table header | `#E2E8F2` | thead background — visually distinct from white tbody and page bg |
| Sidebar background | `#0D1B2A` | Deep navy |
| Sidebar active link | bg `#1B3A5C` · text `#F0F4F8` · `style={{ boxShadow: 'inset 3px 0 0 #EAB308' }}` | Left gold indicator |
| Sidebar hover | bg `#1B3A5C` · text `#CBD5E1` | Hover state |
| Sidebar nav text | `#4A6FA5` | Muted blue-gray |
| Dark text / headings | `#0D1B2A` | Primary text color |
| Muted text | `#4A6FA5` | Section labels, secondary info |
| Conference/filter pill — active | bg `#EFF6FF` · text `#1D4ED8` | Active tab/filter pill |
| Conference/filter pill — count badge | bg `#DBEAFE` · text `#1D4ED8` | Count inside active pill |

### Badge Variants

Use `<AdminBadge variant="…" />` — never hardcode badge markup. Available variants:

| Variant | Appearance | Use for |
|---|---|---|
| `live` | green bg/text | Active/live league status |
| `draft` | blue-gray bg/text | Draft league status |
| `locked` | amber bg/text | Locked state |
| `unlocked` | green bg/text | Unlocked state |
| `classic` | sky bg/text | Classic ROM type |
| `custom` | sky bg/text | Custom ROM type |
| `franchise` | teal bg/text | Franchise mode |
| `tournament` | green bg/text | Tournament mode |
| `king` | amber/gold bg/text | King role |
| `admin` | blue bg/text | League admin role |
| `member` | gray bg/text | Member role (no admin) |
| `new` | green bg/text | New record chip |
| `update` | amber bg/text | Overwrite record chip |
| `error` | red bg/text | Failed operation chip |

Pass `label="…"` to override the default label text. Pass `title="…"` for a tooltip.

### Admin UI Components

All admin pages are built from these components in `src/components/ui/`:

| Component | File | Props | Use for |
|---|---|---|---|
| `AdminPageHeader` | `admin-page-header.tsx` | `title`, `subtitle?`, `action?` | Page title + optional right-side action |
| `AdminButton` | `admin-button.tsx` | `variant` (primary/secondary/danger/ghost), `size` (sm/md/lg), `loading?` | All buttons |
| `AdminInput` | `admin-input.tsx` | `error?`, `hint?`, standard input props | Text inputs; also exports `FormField` with label |
| `AdminToggle` | `admin-toggle.tsx` | `checked`, `onChange`, `disabled?` | Boolean on/off toggles |
| `AdminTable` | `admin-table.tsx` | `minWidth?` | Table container (white card + scroll) |
| `AdminTh` | `admin-table.tsx` | `label`, `field`, `sortKey`, `sortDir`, `onSort`, `align?`, `className?` | Sortable column headers |
| `AdminTr` | `admin-table.tsx` | `selected?` | Table rows — bakes in zebra + hover |
| `AdminBadge` | `admin-badge.tsx` | `variant`, `label?`, `title?` | Status/role badges |
| `AdminModal` | `admin-modal.tsx` | `title`, `onClose`, `footer?`, `maxWidth?` | All modals |
| `AdminSpinner` | `admin-loading.tsx` | — | Full loading state |
| `AdminEmptyState` | `admin-loading.tsx` | `message`, `action?` | Empty list states |

**Sort pattern:** Keep sort state (`sortKey`, `sortDir`, `toggleSort`) in the page via `useSortable` from `@/lib/use-sort`. Pass state down to `AdminTh` — it's purely presentational.

**Tables:** All admin `<tbody>` data rows use zebra stripe via `<AdminTr>` — it bakes in `even:bg-[#DCE5F4]` automatically. Never skip zebra on admin tables. thead background is `#F0F4F9` (applied automatically via `AdminTable`).

**Drop zones** always follow this structure: upload-arrow icon → `"Choose files or drag and drop"` (blue `#1D4ED8` link text) → accepted formats in small muted text below. Active drag state uses blue border + blue/5 background.

### Shared Components (public + admin)

These live in `src/components/` and are used by both sides. Do not mix admin Premium tokens into their styling — they must work in both contexts.

| Component | File | Notes |
|---|---|---|
| `ToastProvider` + `useToast()` | `toast.tsx` | Wrap layout with `<ToastProvider>`. Call `toast('success' \| 'error' \| 'info', title, desc?)` anywhere. Dark slate bg `#1E293B`, left-bar color codes type. |
| `ConfirmModal` | `confirm-modal.tsx` | Distinct from `AdminModal` — has a red-tinted warning header with icon. Use for any destructive action that requires confirmation. Supports `confirmText` prop to require typing a phrase. |
| `UploadModal` | `upload-modal.tsx` | Coach-facing game state file uploader. Admin-only context but built as a shared component. |

### Card Patterns

Three card types appear in the admin. **Cards** represent single entities or choices; **tables** represent lists of uniform rows. Do not use a table for something that is fundamentally a card.

| Pattern | When to use | Structure |
|---|---|---|
| **Option card** | Selectable choice (ROM type, league mode). One active at a time. | White bg, `border-2`, active: `border-[#1D4ED8] bg-white`, inactive: `border-black/10 hover:border-black/25`. Checkmark circle `bg-[#1D4ED8]` when active. Icon + title + desc layout. |
| **Entity card** | A named entity with fields (playoff round, playoff series). | Dark header `bg-[#0D1B2A]` with ALL-CAPS white label (`text-xs font-black tracking-wider`) + trash icon. White body with form fields. |
| **Info card** | Contextual state or prompt with optional CTA (no bracket yet, empty conference). | White card, border, centered content. Not a component — just a `div` with padding and border. |

---

## Technical Setup

- **OS:** Windows 11
- **Node.js 24.11.1** — enforced by `.nvmrc`. Use `nvm use` to switch.
- **pnpm 10.33.0** — `packageManager` in root `package.json` is authoritative (ignore `.tool-versions`). Use `CI=true pnpm install` to avoid interactive store-migration prompts.

---

## Domain Knowledge

**The state parser exists in two places and must be kept in sync.** `src/lib/state-parser.ts` is used by the Next.js app (client-side preview, extractor tool). `supabase/functions/submit-game/state-parser.ts` is the Deno-compatible copy used by the Edge Function. Any change to one must be applied to the other. The duplication exists because Deno cannot import from the Next.js src tree.

**Player name typos in `nhl94-roster-data.ts` are intentional.** Names like `"Alexnder Mogilny"`, `"John Vanbiesbrk"` are transcribed directly from the original ROM. Do not fix them.

**Admin route protection — no middleware needed.** `/admin` uses a client-side auth check that renders only a spinner while verifying; admin UI never flashes to unauthenticated users. The real security boundary is Supabase RLS. Do not add Next.js middleware — it would be redundant. `src/proxy.ts` does not exist and must not be recreated.

**Bootstrapping the first admin account.** The `admins` table has no UI for self-registration — the first king must be inserted directly via the Supabase SQL editor. Steps:
1. Sign up through the app at `/auth/signup` to create a `profiles` row and get an auth UUID
2. Find your UUID: Supabase Dashboard → Authentication → Users
3. Run in SQL Editor:
```sql
INSERT INTO public.admins (user_id, role)
VALUES ('<your-auth-uuid>', 'king');
```
After this you can access `/admin` and manage all leagues. Additional admins can be assigned `league_admin` role through the admin UI.
