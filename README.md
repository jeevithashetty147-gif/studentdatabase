# Student Manager Website

A quick student management website built with:

- HTML
- CSS
- Python Flask
- SQLite database for local development
- PostgreSQL support for Vercel or any hosted deployment

## Features

- Add student
- View student list
- Search student
- Store data in database

## Run the project

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Database

The app automatically creates `students.db` on first run when you run it locally.

## Deploy To Vercel

This project is now structured so Vercel can deploy it directly from the repository:

- `app.py` is the Flask entrypoint
- CSS is served from `public/`
- If `DATABASE_URL` is set, the app uses PostgreSQL for persistent data
- If `DATABASE_URL` is not set on Vercel, the app falls back to `/tmp/students.db`, which works for demos but is not persistent across cold starts

Recommended Vercel setup:

1. Import the repository into Vercel.
2. Leave the framework as `Other`.
3. Add an environment variable named `DATABASE_URL` that points to a PostgreSQL database.
4. Deploy.

If you skip `DATABASE_URL`, the site will still run on Vercel, but student records will be temporary.
