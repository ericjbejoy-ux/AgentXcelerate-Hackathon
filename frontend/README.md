# UI_PART Frontend

This folder contains the vanilla HTML, CSS, and JavaScript demo interface. It runs locally without a backend, API, database, or build step.

## Open the interface

Open `frontend/index.html` in a browser. The first screen is the animated welcome gate. Continue to Login, choose Buyer or Seller, and use the demo credentials shown in the modal.

## Simple edits

- **Welcome text and timing:** edit `startWelcomeAnimation()` in `frontend/script.js`.
- **Welcome colors and layout:** edit `.welcome-screen` and `.welcome-screen h1` in `frontend/styles.css`.
- **Demo accounts:** edit `demoUsers` in `frontend/script.js`.
- **Part categories, names, and IDs:** edit `partCatalog` in `frontend/script.js`.
- **Order form labels and fields:** edit the form markup in `frontend/index.html`.
- **Profile fields and profile layout:** edit `frontend/profile.html` and the matching load/save code in `frontend/profile.js`.
- **Dashboard and profile styling:** edit `frontend/styles.css`.
- **Buyer versus seller behavior:** edit `updateDashboardForRole()` in `frontend/script.js`.

## Local data

Demo users and the active session are stored in browser `localStorage` under `ax_users` and `ax_current_user`. Logging out removes only the active session; saved demo accounts remain available.

## Seller View

1. Open a terminal at the repository root.
2. Install dependencies: `pip install -r requirements.txt`
3. Start the backend: `python -m mocks.supplier_server`
4. Open a second terminal at the repository root.
5. Start the frontend: `python -m http.server 5500 --directory frontend`
6. Open `http://localhost:5500/index.html`
7. Click `Continue to Login`.
8. Select `Seller`.
9. Use `seller@demo.com` and `seller123`.

## Seller Edits

- Backend URL: edit `SELLER_API_BASE_URL` in `script.js`.
- Seller identity: edit the fixed Supplier A markup in `index.html` and `sellerState.supplierId` in `script.js` only if the account changes.
- Catalog display: edit `renderSellerCatalog()` in `script.js`.
- Order display: edit `renderSellerOrders()` in `script.js`.
- Details fields: edit `renderSellerDetails()` in `script.js`.
- Risk fields: edit `renderSellerRisk()` in `script.js`.
- Colors/layout: edit the seller rules near `.seller-command-center` in `styles.css`.

## Seller API Calls

- `GET http://localhost:8001/health`
- `GET http://localhost:8001/supplier_a/catalog`
- `GET http://localhost:8001/seller/orders`
- `POST http://localhost:8001/seller/orders/{order_id}/cancel`

## Seller View Run Steps

1. From the repository root, install dependencies:
	`python3 -m pip install -r requirements.txt`
2. Start FastAPI:
	`.venv/bin/python -m mocks.supplier_server`
3. In a second terminal, serve this folder:
	`python3 -m http.server 5500 --directory frontend`
4. Open:
	`http://localhost:5500/index.html`
5. Log in as Seller:
	`seller@demo.com` / `seller123`
6. The seller account uses Supplier A automatically.

## Browser Requirement

- The backend must allow requests from `http://localhost:5500` with CORS.
- Direct API checks work on `http://localhost:8001`.
- Browser requests remain blocked until the backend enables CORS.