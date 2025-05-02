import dataclasses
import logging
import traceback
from abc import ABC, abstractmethod

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from alerts.toncenter import Toncenter
from database import Database, UserModel


@dataclasses.dataclass
class AlertType:
    name: str
    description: str


ALERTS = {
    "ComplaintsAlert": AlertType(
        "Validator fines",
        "— Validator has been fined in the last validation round"
    ),
    "TelemetryAlert": AlertType(
        "Telemetry",
        """— Node is out of sync
— CPU is overloaded
— Node's db usage is more than 80%
— Network is overloaded
— Disk is overloaded"""
    ),
    "ComplaintsInformation": AlertType(
        "Validators complaints",
        "— All approved complaints for the last validation round"
    ),
    "ElectionsInformation": AlertType(
        "Elections",
        "— Alerts for validator's sent (or not sent) stakes"
    )
}


class Alert(ABC):

    disable_notification = False

    def __init__(self, toncenter: Toncenter, database: Database, bot: Bot, *args, **kwargs):
        self.toncenter: Toncenter = toncenter
        self.database: Database = database
        self.bot: Bot = bot
        self.alert_type: str = self.__class__.__name__
        self.logger = logging.getLogger(self.alert_type)

    async def get_users(self):
        return await self.database.get_users_with_enabled_alert(self.alert_type)

    async def run(self):
        self.logger.info(f'Alert {self.alert_type} running is started.')
        try:
            users = await self.get_users()
            if not users:
                return
            await self.check(users)
        except Exception as e:
            self.logger.warning(f"Error in alert: {e}\n{traceback.format_exc()}")
        self.logger.info(f'Alert {self.alert_type} running is done.')

    async def send_message(self, user_id: int, text: str) -> None:
        try:
            buttons = [[InlineKeyboardButton(text=f"Disable {ALERTS[self.alert_type].name} Alerts", callback_data=f"alert:disable_no_edit:{self.alert_type}")]]
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            await self.bot.send_message(chat_id=user_id, text=text, disable_notification=self.disable_notification, reply_markup=markup)
        except Exception as e:
            self.logger.warning(f"Failed to send message to {user_id}: {e}")
            return

    @abstractmethod
    async def check(self, users: list[UserModel]) -> None:
        pass

    async def inform(self, user: UserModel, alert_name: str, text: str):
        triggered_alerts = await self.database.get_triggered_alerts(user.user_id, alert_name)
        if triggered_alerts:
            return
        await self.send_message(user.user_id, text)
        await self.database.add_triggered_alert(user.user_id, alert_name)
        self.logger.info(f"Sent alert {alert_name} to user {user.user_id}")
