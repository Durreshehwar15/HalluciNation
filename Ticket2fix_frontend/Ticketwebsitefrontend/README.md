# Ticket2Fix – Frontend (no GitHub needed)

Storybook-style React website for "Support Ticket to Merged Fix".
It runs on built-in sample data, so you do not need the backend to try it.

## Run it (Windows, Mac or Linux)

1. Install **Node.js 18 or newer** from https://nodejs.org (once).
2. Unzip this folder.
3. Open a terminal inside the `frontend` folder and run:
   ```
   npm install
   npm run dev
   ```
   Or just double-click `run.bat` (Windows) / run `./run.sh` (Mac/Linux).
4. Open http://localhost:5173

## Pages
- `/` Home (story landing page)
- `/guide` Website guide (steps, status meanings, FAQ)
- `/tickets` Ticket list · `/submit` New ticket
- `/tickets/:id` Agent progress · `/tickets/:id/approve` Patch review and approval

## Connect to the real backend later
Copy `.env.example` to `.env` and set:
```
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000
```
The FastAPI server must allow CORS from http://localhost:5173.

## API contract
- POST /tickets · GET /tickets · GET /tickets/{id}
- POST /tickets/{id}/approve · POST /tickets/{id}/reject  (body: { feedback })

Statuses: submitted, triage, investigating, fixing, testing, review, awaiting_approval, approved, pr_created, merged, rejected
Event: { agent, message, timestamp, evidence? }
Ticket: { id, title, description, status, created_at, events[], patch{file,diff}, test_results{passed,failed,total,cases[]}, review{verdict,comments[]}, pr_url }

## Edit the text
- Guide content: `src/content/guide.js`
- Agent names and descriptions: `src/content/agents.js`
- Landing page: `src/pages/Home.jsx`
