from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from handlers.utils import TEXTS
from database import Database

menu_router = Router(name=__name__)


@menu_router.message(CommandStart())
async def command_start_handler(message: Message, db_manager: Database) -> None:
    if await db_manager.get_user_nodes(message.from_user.id):
        await main_menu(message)
        return
    text = TEXTS['start']
    buttons1 = [
        InlineKeyboardButton(text='Add Node', callback_data='add_node'),
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons1])
    await message.answer(text, reply_markup=markup)
    await db_manager.add_user_with_alerts(message.from_user.id, message.from_user.username)

@menu_router.callback_query(lambda c: c.data == 'main_menu')
async def main_menu_callback_handler(callback_query: CallbackQuery) -> None:
    await callback_query.answer()
    await main_menu(callback_query)


async def main_menu(message: Message | CallbackQuery) -> None:
    buttons1 = [
        InlineKeyboardButton(text='Add Node', callback_data='add_node'),
        InlineKeyboardButton(text='My Nodes', callback_data='my_nodes'),
    ]
    buttons2 = [
        InlineKeyboardButton(text='Notifications', callback_data='notifications'),
    ]
    buttons3 = [
        InlineKeyboardButton(text='Validators Support', url='https://t.me/validators_help_bot'),
    ]
    buttons4 = [
        InlineKeyboardButton(text='Node Help Group', url='https://t.me/ton_node_help'),
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons1, buttons2, buttons3, buttons4])
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text=TEXTS['main_menu'], reply_markup=markup, disable_web_page_preview=True)
    else:
        await message.answer(text=TEXTS['main_menu'], reply_markup=markup, disable_web_page_preview=True)
