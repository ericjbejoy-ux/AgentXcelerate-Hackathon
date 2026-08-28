# AutoSCM — React Frontend

Component-based React (Vite + Tailwind CSS) UI for the AutoSCM fulfillment engine.
A full replacement for the original vanilla-JS `frontend/` dashboard.

## Run

The React dev server runs on **`http://localhost:5173`** and proxies API calls to the
FastAPI backend (default **`http://localhost:8100`**).

```bash
# 1. Start the backend (FastAPI) if not already running
cd /home/daya/Development/AgentXcelerate-Hackathon
python3 scripts/start_backend.py --port 8100

# 2. Install deps (first time only)
cd frontend-react && npm install

# 3. Start the Vite dev server
cd /home/daya/Development/AgentXcelerate-Hackathon
python3 scripts/start_frontend.py --port 5173
```

Open `http://localhost:5173/`. Log in with buyer@demo.com / buyer123.

### Production build

```bash
cd frontend-react && npm run build   # outputs to dist/
npm run lint                          # oxlint
```

`npm run preview` serves the production build locally.

## Structure (component-based, easy to add/remove pages)

```
frontend-react/
  vite.config.js          # dev proxy → backend :8100
  index.html              # HTML entry (loads src/main.jsx)
  src/
    main.jsx              # React bootstrap (StrictMode)
    App.jsx               # Top-level: auth gate + page router (PAGES map)
    index.css             # Tailwind directives + custom styles/pipeline animation
    api/client.js         # API helpers + static data (part catalog, users, pipeline steps)
    contexts/
      AuthContext.jsx     # user session (login/signup/logout), localStorage-backed
    components/
      Layout.jsx          # topbar: logo, nav tabs, online status, user pill, logout
      WelcomeScreen.jsx   # animated landing screen
      AuthModal.jsx       # Buyer/Seller login + demo autofill
      Pipeline.jsx        # animated multi-agent pipeline (Orchestrator → Geo Routing → ...)
      Results.jsx         # winner card + AI explanation + candidates table
    pages/
      NewOrder.jsx        # fulfillment form + GPS/city + pipeline + results
      Analytics.jsx       # summary cards + distributions + recent orders
      Inventory.jsx       # live warehouse stock table + stats
      History.jsx         # previous orders table
      Info.jsx            # architecture / pipeline / weights / tech stack
```

## Adding or removing a page (component-based)

Each page is a single component in `src/pages/`. To add a new page:

1. Create `src/pages/MyPage.jsx` exporting a default component.
2. Register it in `src/App.jsx`'s `PAGES` map (add a key, e.g. `mypage`).
3. Add a nav tab in `src/components/Layout.jsx`'s `NAV_TABS` array.

To remove a page, delete its file, remove the entry from `PAGES`, and drop its
`NAV_TABS` entry. No other wiring is required.

## Calling the backend

Use the helpers in `src/api/client.js` (`api.health()`, `api.processOrder()`,
`api.inventory()`, `api.analytics()`, `api.orders()`, `api.approve()`). Requests
are made relative (`/api/...`) and forwarded to the backend by the Vite dev proxy.
