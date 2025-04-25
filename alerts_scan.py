import asyncio
import logging

from aiogram import Bot

from alerts.toncenter import Toncenter
from database import Database
from alerts import ComplaintsAlert, TelemetryAlert, ElectionsInformation, ComplaintsInformation


async def run_alerts_scanner(toncenter, db, bot):
    while True:
        try:
            await scan(toncenter, db, bot)
            await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"Error in alerts scanner: {e}")
            await asyncio.sleep(10)


async def scan(toncenter: Toncenter, db_manager: Database, bot: Bot):
    alerts = [
        ComplaintsAlert(toncenter, db_manager, bot),
        TelemetryAlert(toncenter, db_manager, bot),
        ElectionsInformation(toncenter, db_manager, bot),
        ComplaintsInformation(toncenter, db_manager, bot),
    ]
    tasks = []
    for alert in alerts:
        tasks.append(alert.run())

    await asyncio.gather(*tasks, return_exceptions=True)
