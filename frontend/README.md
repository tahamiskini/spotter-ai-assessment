# HOS Trip Planner — Frontend

React + Vite + TypeScript client for the HOS (Hours of Service) truck trip
planner. Given a trip, it renders an HOS-compliant schedule, an interactive
route map, and daily ELD-style log sheets.

## Tech stack

- **Vite + React 18 + TypeScript** (strict), `@/*` path alias
- **@tanstack/react-query** for data fetching (query-options + hook pattern)
- **axios** API client (`src/lib/api-client.ts`)
- **react-hook-form + zod** for forms and validation
- **Tailwind CSS** with shadcn-style tokens
- **react-leaflet + OpenStreetMap** tiles for the map
- **MSW** for mocking, **Vitest** + **Playwright** for tests, **Storybook**
  for components, **plop** for component generation

## Architecture (bulletproof-react)

```
src/
  app/          # bootstrap: provider, router, routes
  components/   # ui primitives, layouts, errors, seo
  config/       # env (zod-validated) + route paths
  features/     # feature modules (trips) -> api + components
  lib/          # api-client, react-query config
  testing/      # MSW mocks + test utils
  types/        # API types shared with the backend
  utils/        # cn, formatters
```

## Get started

```bash
pnpm install
cp .env.example .env   # point VITE_APP_API_URL at the Django API
pnpm dev               # http://localhost:3000
```

Other scripts: `pnpm build`, `pnpm check-types`, `pnpm test`, `pnpm lint`,
`pnpm storybook`, `pnpm generate` (scaffold a new component).
