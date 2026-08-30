# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is an **IELTS Mock Test admin panel** — a React SPA for managing IELTS mock tests and their sections. The UI is built on the [shadcn-admin](https://github.com/satnaing/shadcn-admin) template. The entire frontend lives in the `frontend/` subdirectory.

## Commands

All commands must be run from the `frontend/` directory.

```bash
npm run dev              # start Vite dev server
npm run build            # tsc type-check + Vite production build
npm run lint             # ESLint
npm run format           # Prettier (write)
npm run format:check     # Prettier (check only)
npm run knip             # dead code detection
npm run test             # Vitest, headless Chromium (one-shot)
npm run test:watch       # Vitest watch mode
npm run test:coverage    # Vitest with coverage report
```

**First-time setup**: run `npm run test:browser:install` once to install the Playwright Chromium binary before running any tests.

To run a single test file:
```bash
npx vitest run src/path/to/file.test.tsx --browser.headless
```

## Architecture

### Routing

TanStack Router with **file-based routing** (`@tanstack/router-plugin/vite` auto-generates `src/routeTree.gen.ts` — never edit this file manually). Route groups:

- `src/routes/(auth)/` — public auth pages (sign-in, sign-up, OTP, forgot-password)
- `src/routes/(errors)/` — standalone error pages
- `src/routes/_authenticated/` — all protected routes; the layout route at `_authenticated/route.tsx` checks for a JWT via `useAuthStore` and redirects to `/sign-in` if missing
- `src/routes/clerk/` — alternative Clerk-based auth flow

### State management

Two layers:
1. **Server state** — TanStack Query (`@tanstack/react-query`). The `QueryClient` is defined in `main.tsx` and passed as router context. Global 401 handling in `QueryCache.onError` clears the auth token and redirects to sign-in.
2. **Client state** — Zustand. Only one store: `src/stores/auth-store.ts`, which persists the JWT access token in a browser cookie.

### API layer

`src/lib/axios.ts` creates an Axios instance that reads `VITE_API_URL` from env and injects the Bearer token from `useAuthStore` on every request.

API functions are colocated in `src/lib/api/`:
- `admin.ts` — login (`POST /admin/auth/login`), current user (`GET /admin/auth/me`), JWT decode helper
- `tests.ts` — CRUD for `Test` entities (`/admin/tests/`)
- `sections.ts` — update a `Section` (`PATCH /admin/sections/:id`)

### Feature structure

`src/features/<name>/` follows a consistent pattern:
- `index.tsx` — page component (fetches data via `useQuery`, composes sub-components)
- `data/schema.ts` — TypeScript types (and Zod schemas where needed)
- `data/*.ts` — static/seed data or additional typed helpers
- `components/` — feature-specific components:
  - `*-provider.tsx` — React context that tracks which dialog is open and which row is selected (`useDialogState` hook)
  - `*-dialogs.tsx` — mounts all dialogs for the page, driven by context
  - `*-action-dialog.tsx` — shared create/edit form dialog
  - `*-delete-dialog.tsx`, `*-multi-delete-dialog.tsx`
  - `*-table.tsx`, `*-columns.tsx`, `*-primary-buttons.tsx`

The **Tests** feature is the domain-specific one: manages `Test` records (title, description, is_published) and their `Section` records (type: listening | reading | writing | speaking, duration_minutes, audio_url). Navigating to `/tests/:testId` renders `TestDetail`, which shows sections and allows editing via `SectionEditDialog`.

### Forms pattern

All forms use: **Zod schema → `useForm` with `zodResolver` → shadcn `Form` components → `useMutation` → `queryClient.invalidateQueries` on success**.

### Layout

`AuthenticatedLayout` (`src/components/layout/authenticated-layout.tsx`) wraps all `_authenticated` routes. It provides `SearchProvider`, `LayoutProvider`, and shadcn's `SidebarProvider`. The sidebar menu is defined in `src/components/layout/data/sidebar-data.ts`.

### UI components

`src/components/ui/` contains shadcn/ui components — treat these as library code. They are excluded from ESLint, TypeScript `noUnusedLocals`, and test coverage.

The `@` path alias resolves to `src/`.

## ESLint rules to be aware of

- `no-console: error` — use `if (import.meta.env.DEV) console.log(...)` guards
- `@typescript-eslint/consistent-type-imports: error` — always use `import type { Foo }` for type-only imports
- Unused variables must be prefixed with `_` to silence the error
- `src/components/ui/` is excluded from linting entirely

## Environment variables

| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Base URL for the backend REST API |

## Adding a full mock from a PDF / book

There is **no admin PDF upload**. Author seed scripts + media, then publish on the VPS.

**Follow:** [`backend/scripts/SEED_FROM_PDF.md`](backend/scripts/SEED_FROM_PDF.md)

Summary:

1. Copy Practice Set B Test 1 (`seed_practice_b_t1_*.py`) or Set A seeds as the template.
2. Add `data/practice_*_t{N}/` passages + `sections.json`, and gitignored mp3/png under `backend/media/`.
3. Seed locally: bootstrap → listening → reading → writing → speaking → `verify_*` → `check_*_scoring`.
4. `git push main` only ships **code**. Content on prod: stage files + `deploy_practice_b.sh {N} --publish` (docker cp into `ielts-mock-backend-1`).
5. Never show Longman / Plus 2 / Cambridge book titles to students; omit Tip Strips.
