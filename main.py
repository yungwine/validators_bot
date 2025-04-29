import asyncio
import logging
import os
import sys
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from bot import run_bot
from alerts_scan import run_alerts_scanner
from alerts.toncenter import Toncenter
from database import Database


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    load_dotenv()

    bot_token = os.getenv('BOT_TOKEN')
    api_key = os.getenv('TONCENTER_API_KEY')
    database_url = os.getenv('DATABASE_URL')
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is not set")

    db = Database(database_url)
    await db.init_db()

    toncenter = Toncenter(api_key)

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    asyncio.create_task(
        run_alerts_scanner(toncenter, db, bot)
    )
    await run_bot(bot, db, toncenter)
    # await asyncio.gather(alerts_task, bot_task)


if __name__ == "__main__":
    asyncio.run(main())
