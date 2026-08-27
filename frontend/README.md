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