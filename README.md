# Validators bot

This project is modern version of the bot for validators operators to monitor their nodes performance.
Public bot is available at [@validators](https://t.me/validators).

## Install

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create .env file

```dotenv
BOT_TOKEN=<BOT_TOKEN>
TONCENTER_API_KEY=<TONCENTER_API_KEY>
DATABASE_URL=<DATABASE_URL>
ADMIN_USERS=<ADMIN_USER_IDS_SEPARATED_BY_SPACE>
```

### Run

```bash
python3 main.py
```