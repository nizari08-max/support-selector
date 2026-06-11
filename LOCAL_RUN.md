# Running the app locally on Windows

## Quick start

Double-click **`run_local.bat`** in the project folder.

The launcher will:
1. Activate `.venv` if it exists, or fall back to your system Python.
2. Check that the required packages are installed; install them automatically if any are missing.
3. Start the Flask server on `http://127.0.0.1:5000`.
4. Open that address in your default browser automatically.

The terminal window stays open so you can see request logs and any errors.

---

## Stopping the server

Press **Ctrl + C** in the terminal window. The window will show `Server has stopped.` and wait for a keypress before closing.

---

## Troubleshooting

### "Python was not found on PATH"

Python is either not installed or not on the system PATH.

1. Download from <https://www.python.org/downloads/>.
2. During installation, check **"Add Python to PATH"**.
3. Re-run `run_local.bat`.

### "pip install failed"

Open a terminal in the project folder and run:

```
python -m pip install -r requirements.txt
```

If your organisation blocks pip from the internet, install the packages manually or configure a proxy:

```
python -m pip install --proxy http://proxy:port -r requirements.txt
```

### Packages are present but the app crashes on startup

Check the error message in the terminal. Common causes:

- **Port 5000 already in use** — another process is using the port. Either stop it or edit `run_local.bat` and change `set PORT=5000` to another port (e.g. `5001`), then also update the browser URL.
- **PDF not found** — `QW2507-00-PE-STD-00001.pdf` must be in the project root for drawing lookups to work. The app starts without it but the `/api/drawing/…` endpoint will return 404.

### Using a virtual environment

To create `.venv` yourself (recommended):

```
python -m venv .venv
run_local.bat
```

The launcher will detect and activate it automatically on every subsequent run.
