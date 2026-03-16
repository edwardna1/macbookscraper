# Apple Canada Refurbished MacBook Pro Monitor

Lightweight monitor that watches Apple Canada’s refurbished Mac store for **MacBook Pro** deals matching:

- **MacBook Pro:** M4 Pro, M3 Pro, or M2 Pro with **24GB+ RAM**
- **MacBook Air:** M4 with **32GB+ RAM**

It ranks matches by value, avoids duplicate alerts using a local JSON store, and can notify you via **Telegram** for new matches or price drops.

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

3. **Configure Telegram and options:**

   Copy `.env.example` to `.env` and set:

   - `TELEGRAM_BOT_TOKEN` – from [@BotFather](https://t.me/BotFather) (send `/newbot`, follow prompts)
   - `TELEGRAM_CHAT_ID` – your chat ID (start a chat with your bot, then e.g. visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and look for `"chat":{"id": ... }`)

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

Without Telegram configured, the monitor still runs and logs what it would have alerted.

## Project layout

| File        | Role |
|------------|------|
| `monitor.py` | Main loop: fetch → parse → filter → rank → storage → alert |
| `parser.py`  | Fetch Apple refurb listing and product detail pages; normalize to structured products |
| `filters.py` | MacBook Pro 24GB+ (M2/M3/M4 Pro) or MacBook Air M4 32GB+ |
| `ranker.py`  | Value score and sort; mark best current deal |
| `alerts.py`  | Telegram Bot message formatting and send |
| `storage.py` | JSON file: seen product IDs, last price, last alerted (for new vs price-drop alerts) |
| `config.py`  | Settings from env (`.env` via python-dotenv) |

## GitHub Actions (run in the cloud, no laptop needed)

The workflow runs every 5 minutes on GitHub’s servers, so **you don’t need your laptop on or WiFi** — it uses GitHub’s internet to fetch Apple and send Telegram.

**Setup:**

1. In your repo go to **Settings → Secrets and variables → Actions**.
2. **New repository secret** for each:
   - `TELEGRAM_BOT_TOKEN` (from BotFather)
   - `TELEGRAM_CHAT_ID` (your numeric chat ID, e.g. from `python get_chat_id.py`)
3. Open the **Actions** tab, select **Refurb Monitor**, and run **Enable workflow** if it’s disabled.

**Persistence:** The workflow commits `seen_products.json` back into the repo after each run. That way the next run sees what was already alerted, so you only get Telegram alerts for **new** listings or **price drops**, not the same deals every 5 minutes.

## Notes

- **No browser automation** – HTTP only; no checkout or cart.
- **Storage** – `seen_products.json` (or `STORAGE_PATH`) stores product URL, last price, first/last seen and last alerted timestamps so you only get one alert per new listing (and again on price drop).
- **Detail pages** – RAM/SSD are read from each MacBook Pro M2/M3/M4 Pro product page so only those matching chip type get extra requests.
- **Internet** – The script needs the internet to fetch Apple and send Telegram. When you use **GitHub Actions**, that happens on GitHub’s servers, so your laptop and WiFi don’t need to be on.
