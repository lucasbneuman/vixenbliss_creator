# API Breaking Change Policy (v1 Stable)

Effective date: 2026-02-12
Scope: endpoints documented in `docs/api-contracts/v1_endpoints.md`

## 1) Versioning rule
- `/api/v1/*` is stable.
- Any breaking change must ship in a new versioned path (`/api/v2/*`), never by mutating existing v1 contracts.
- Breaking changes include: removing/renaming endpoints, changing HTTP method, removing/renaming required fields, changing field type, changing success status code class/expectation, or changing auth requirements.

## 2) Change strategy
- Prefer additive changes in v1 only:
  - new optional request fields
  - new optional response fields
  - new endpoints (without changing existing ones)
- For behavior changes that may alter client assumptions, gate rollout with feature flags.
- For incompatible behavior, create new versioned endpoints and keep v1 unchanged during migration.

## 3) Deprecation policy
- Deprecate only after a successor exists (`/api/v2/*` or equivalent).
- Minimum coexistence window: 6 months.
- Announce deprecation in docs and release notes with concrete dates.
- Recommended response headers during deprecation:
  - `Deprecation: true`
  - `Sunset: <HTTP-date>`
  - `Link: </api/v2/...>; rel="successor-version"`
- After sunset, remove deprecated version only if migration window was honored.

## 4) PR/Review requirements for API changes
- Update `docs/api-contracts/v1_endpoints.md` if contract surface is touched.
- Add/adjust contract tests in `backend/tests/test_api_contracts.py`.
- Run test suite and attach results in PR.
