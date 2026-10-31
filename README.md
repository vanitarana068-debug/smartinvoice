# Smart Invoice AI

A private business finance workspace for invoicing, customer management, expenses, payments, cash-basis profit and loss, cash flow, reminders, analytics, and AI-assisted financial insights.

## Supabase setup

The app uses Supabase Auth and Postgres. Before launching it for the first time, open your project's SQL Editor and run [`supabase/schema.sql`](./supabase/schema.sql). The migration creates the finance tables, indexes, and per-user row-level security policies. Do not disable RLS.

The local `.env` file contains `SUPABASE_URL` and `SUPABASE_ANON_KEY`. The publishable/anon key is used only by the local server; users' Supabase access tokens are stored in HTTP-only cookies, and Postgres requests run under those tokens so RLS remains active. **Never add a `service_role` or secret key to this app.** `.env` is ignored by Git.

If a `service_role` key was ever shared or exposed, rotate it in Supabase before continuing. This application does not need it.

If configuring a different machine, copy `.env.example` to `.env` and set your project URL and publishable key. Requires Python 3.10 or later; no third-party Python packages are needed.

```powershell
python server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and create an account. If Supabase email confirmation is enabled, confirm the registration email before signing in. The development server binds to localhost; use HTTPS and set `COOKIE_SECURE=1` for a production deployment. Set `PORT` in `.env` to change the port.

The previous local SQLite database is not automatically copied to Supabase. It contained no account or finance records when the migration was started.

## Gemini business analysis

AI insights and business signals are calculated from the signed-in user's actual Supabase records. To enable Gemini-written analysis, add `GEMINI_API_KEY=your-Gemini-API-key` to the local `.env` file, then restart the server.

The Gemini key never enters the browser or the database. A Gemini request is initiated only when a signed-in user selects **Ask Gemini**. Only six-month aggregate financial figures, growth rates, and aggregated expense and service category totals are sent. Customer names and contact details, invoice numbers and descriptions, and transaction-level records stay on the server. Gemini's responses are financial observations, not tax, legal, or professional financial advice.

## Financial definitions

Revenue means payments actually recorded as received, not merely issued invoices. Profit and loss uses cash-basis accounting: payments received less expenses recorded during the selected period. Outstanding invoice balances are shown separately and are not treated as cash or revenue. Invoices can be printed or saved as a PDF for sharing. Payment reminders are recorded in the workspace for follow-up; **the app does not send emails**.

For an estimated current cash balance and low-cash warnings, enter your opening bank balance and the date it applies in **Settings**. Only payments and expenses recorded on or after that date adjust the starting balance. This is an estimate, not a live bank connection. Until an opening balance is provided, the app clearly shows the estimate as unset rather than assuming it is zero.

Supabase stores and backs up the database in your project. The app does not import data from the old local SQLite file. Protect your Supabase account with MFA and configure project backups and email authentication settings appropriately.

## Tests

```powershell
python -m unittest -v
```
