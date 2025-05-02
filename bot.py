import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from alerts.toncenter import Toncenter
from database import Database
from handlers import (add_node_router, menu_router, edit_node_router, notifications_router, admin_router,
                      TEXTS, add_adnl_message_handler, add_label_message_handler)

from dotenv import load_dotenv

from handlers.edit_nodes import edit_label_message_handler

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
admin_users = list(map(int, os.getenv('ADMIN_USERS', '').split()))


router = Router(name=__name__)


async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(command='start', description='Bot Start'),
    ]
    await bot.set_my_commands(
        commands, scope=BotCommandScopeAllPrivateChats()
    )


async def on_startup(bot: Bot):
    await set_default_commands(bot)


@router.message()
async def message_handler(message: Message, db_manager: Database, toncenter: Toncenter) -> None:
    user_state = await db_manager.get_user_state(message.from_user.id)
    if user_state == 'add_node':
        await add_adnl_message_handler(message, db_manager, toncenter)
    elif user_state.startswith('add_label'):
        await add_label_message_handler(message, db_manager)
    elif user_state.startswith('edit_label'):
        await edit_label_message_handler(message, db_manager)
    else:
        await message.answer(text=TEXTS['unknown_command'])


async def run_bot(bot: Bot, db: Database, toncenter: Toncenter) -> None:
    # bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # db = Database()
    # await db.init_db()

    dp = Dispatcher(session_maker=None, db_manager=db, toncenter=toncenter, admin_users=admin_users)
    dp.include_router(menu_router)
    dp.include_router(edit_node_router)
    dp.include_router(notifications_router)
    dp.include_router(add_node_router)
    dp.include_router(admin_router)
    dp.include_router(router)

    dp.startup.register(set_default_commands)
    dp.shutdown.register(db.close)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(run_bot())
