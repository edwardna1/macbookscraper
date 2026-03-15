# Apple Canada Refurbished MacBook Pro Monitor

Lightweight monitor that watches Apple Canada’s refurbished Mac store for **MacBook Pro** deals matching:

- **M4 Pro**, **M3 Pro**, or **M2 Pro** with **36GB+ RAM**

It ranks matches by value, avoids duplicate alerts using a local JSON store, and can notify you via **Twilio SMS** for new matches or price drops.

## Setup

1. **Python 3.10+** and create a virtualenv (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # or: source .venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Twilio and options:**

   Copy `.env.example` to `.env` and set:

   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` – from [Twilio Console](https://console.twilio.com)
   - `TWILIO_FROM_NUMBER` – your Twilio phone number (e.g. `+1234567890`)
   - `TWILIO_TO_NUMBER` – your phone number to receive SMS (e.g. `+1234567890`)

   Optional:

   - `POLL_INTERVAL_MINUTES` – default `12`
   - `STORAGE_PATH` – default `seen_products.json`

## Usage

- **Run once** (e.g. for cron or GitHub Actions):

  ```bash
  python monitor.py --once
  ```

- **Run continuously** (polls every 10–15 minutes):

  ```bash
  python monitor.py
  ```

Without Twilio configured, the monitor still runs and logs what it would have alerted.

## Project layout

| File        | Role |
|------------|------|
| `monitor.py` | Main loop: fetch → parse → filter → rank → storage → alert |
| `parser.py`  | Fetch Apple refurb listing and product detail pages; normalize to structured products |
| `filters.py` | Keep only MacBook Pro, M2/M3/M4 Pro, RAM ≥ 36GB |
| `ranker.py`  | Value score and sort; mark best current deal |
| `alerts.py`  | Twilio SMS formatting and send |
| `storage.py` | JSON file: seen product IDs, last price, last alerted (for new vs price-drop alerts) |
| `config.py`  | Settings from env (`.env` via python-dotenv) |

## GitHub Actions (optional)

To run on a schedule (e.g. every 5 minutes), add a workflow and secrets:

- In the repo: **Settings → Secrets and variables → Actions**, add:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`
  - `TWILIO_TO_NUMBER`

Then use the workflow in `.github/workflows/monitor.yml` (see that file for the schedule).

## Notes

- **No browser automation** – HTTP only; no checkout or cart.
- **Storage** – `seen_products.json` (or `STORAGE_PATH`) stores product URL, last price, first/last seen and last alerted timestamps so you only get one alert per new listing (and again on price drop).
- **Detail pages** – RAM/SSD are read from each MacBook Pro M2/M3/M4 Pro product page so only those matching chip type get extra requests.
