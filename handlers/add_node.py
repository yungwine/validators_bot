from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from alerts.toncenter import Toncenter
from database import Database
from handlers.utils import TEXTS
from handlers.menu import main_menu


MAX_NODES_PER_USER = 500

add_node_router = Router(name=__name__)

@add_node_router.callback_query(lambda c: c.data == 'add_node')
async def add_adnl_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    await callback_query.answer()
    await callback_query.message.edit_text(text=TEXTS['add_node'], disable_web_page_preview=True)
    await db_manager.set_user_state(callback_query.from_user.id, 'add_node')


def check_adnl_valid(adnl: str):
    try:
        int(adnl, 16)
        is_hex = True
    except:
        is_hex = False
    if not is_hex or len(adnl) != 64:
        return False
    return True


async def add_adnl_message_handler(message: Message, db_manager: Database, toncenter: Toncenter) -> None:
    adnl = message.text.upper()
    return await add_adnl(adnl, message, db_manager, toncenter)

async def add_adnl(adnl: str, message: Message, db_manager: Database, toncenter: Toncenter):
    if not check_adnl_valid(adnl):
        await message.answer(text=TEXTS['wrong_adnl'])
        return
    nodes = await db_manager.get_user_nodes(message.from_user.id)
    if len(nodes) > MAX_NODES_PER_USER:
        await message.answer(text=TEXTS['too_many_nodes'].format(limit=MAX_NODES_PER_USER))
        return
    for node in nodes:
        if node.adnl == adnl:
            await message.answer(text=TEXTS['node_already_exists'])
            return
    await db_manager.add_node(message.from_user.id, adnl)
    await db_manager.set_user_state(message.from_user.id, f'add_label:{adnl}')
    buttons1 = [
        InlineKeyboardButton(text='Skip', callback_data='skip_add_label'),
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons1])
    send_telemetry = await toncenter.is_send_telemetry(adnl)
    text = TEXTS['node_added']
    if not send_telemetry:
        text += TEXTS['node_telemetry_not_send']
    await message.answer(text, reply_markup=markup)


async def set_label(message: Message, db_manager: Database) -> None:
    user_state = await db_manager.get_user_state(message.from_user.id)
    label = message.text
    adnl = user_state.split(':')[1]
    if len(label) > 32:
        await message.answer(text=TEXTS['wrong_label'])
        return
    await db_manager.set_node_label(message.from_user.id, adnl, label)
    await db_manager.set_user_state(message.from_user.id, '')

async def add_label_message_handler(message: Message, db_manager: Database) -> None:
    await set_label(message, db_manager)
    await message.answer(text=TEXTS['node_label_added'])
    await main_menu(message)


@add_node_router.callback_query(lambda c: c.data == 'skip_add_label')
async def add_adnl_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    await callback_query.answer()
    await callback_query.message.edit_text(text=TEXTS['node_label_added'])
    await db_manager.set_user_state(callback_query.from_user.id, '')
    await main_menu(callback_query.message)
