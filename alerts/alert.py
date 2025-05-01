import dataclasses
import logging
import traceback
from abc import ABC, abstractmethod

from aiogram import Bot

from alerts.toncenter import Toncenter
from database import Database, UserModel


@dataclasses.dataclass
class AlertType:
    type: str
    name: str
    description: str


ALERTS = [
    AlertType("ComplaintsAlert", "Validator fines", "Alert for validator fines"),
    AlertType("TelemetryAlert", "Telemetry", "Alert for telemetry data"),
    AlertType("ComplaintsInformation", "Validators complaints", "Alert for complaints on network validators"),
    AlertType("ElectionsInformation", "Elections", "Alert for validators sending stakes"),
]


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
            await self.bot.send_message(chat_id=user_id, text=text, disable_notification=self.disable_notification)
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
