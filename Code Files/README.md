# FitBuddy – AI Fitness Plan Generator

A FastAPI + Jinja2 + SQLite web application that follows the supplied FitBuddy project documentation. It collects a user's profile, generates a structured 7-day workout plan with Gemini, generates a short nutrition/recovery tip, and lets the user submit feedback to regenerate the plan.

## What is included

- FastAPI backend and HTML/Jinja2 frontend
- SQLAlchemy + SQLite persistence
- Google Gemini integration using the current `google-genai` SDK
- Structured JSON output for reliable 7-day plans
- Feedback-based plan regeneration
- Nutrition/recovery tip generation
- Basic HTTP Basic authentication for the admin dashboard
- REST API endpoints plus browser pages
- Demo mode for running the UI without an API key
- Automated API tests

## Project structure

```text
fitbuddy/
├── app/
│   ├── __init__.py
│   ├── ai.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── schemas.py
│   └── services.py
├── data/
│   └── .gitkeep
├── static/
│   ├── app.js
│   └── styles.css
├── templates/
│   ├── all_users.html
│   ├── base.html
│   ├── error.html
│   ├── index.html
│   └── result.html
├── tests/
│   └── test_app.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## 1. VS Code setup

1. Install Python 3.11+.
2. Open this folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows CMD

```bat
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

5. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Copy `.env.example` to `.env`.

## 2. Configure Gemini

Create a Gemini API key and put it in `.env`:

```env
GEMINI_API_KEY=your_real_key_here
```

The application uses:

```env
GEMINI_WORKOUT_MODEL=gemini-3.1-pro-preview
GEMINI_TIP_MODEL=gemini-3.8-flash
```

These values are configurable so the project does not hard-code a model that may later change availability.

## 3. Run in demo mode first

For a first UI test, you can avoid Gemini entirely:

```env
DEMO_MODE=true
```

Then run:

```bash
python run.py
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

## 4. Run with Gemini

Set:

```env
DEMO_MODE=false
GEMINI_API_KEY=your_real_key_here
```

Then:

```bash
python run.py
```

## 5. Test the application

Run the automated tests:

```bash
pytest -q
```

The tests use demo mode, so they do not call Gemini and do not require an API key.

## Main routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | User input form |
| `/generate-workout` | POST | Generate and save plan |
| `/submit-feedback` | POST | Regenerate plan from feedback |
| `/view-all-users` | GET | Protected admin dashboard |
| `/api/health` | GET | Health check |
| `/api/users/{user_id}` | GET | Get saved user/plan data |
| `/docs` | GET | FastAPI Swagger UI |

## Admin dashboard

The admin page uses HTTP Basic authentication. Set these in `.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
```

Then visit `/view-all-users` and enter those credentials.

## Notes on the supplied specification

The supplied document names `google-generativeai` and Gemini 1.5 Pro/Flash. This implementation preserves the intended architecture and responsibilities but uses the newer `google-genai` SDK and configurable current model names. The AI layer also requests structured JSON so the application can reliably render seven daily entries instead of depending on free-form text formatting.

## Safety note

FitBuddy is an educational wellness-planning application, not a medical diagnosis or treatment system. The prompts explicitly avoid medical claims, extreme exercise, crash dieting, or unsafe weight-control instructions. Users with injuries, medical conditions, or significant exercise restrictions should seek advice from an appropriately qualified adult/health professional.
