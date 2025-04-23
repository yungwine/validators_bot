from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio

from database import Database
from handlers.utils import TEXTS

edit_node_router = Router(name=__name__)


@edit_node_router.callback_query(lambda c: c.data == 'my_nodes')
async def my_nodes_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    await callback_query.answer()
    nodes = await db_manager.get_user_nodes(callback_query.from_user.id)

    buttons = []
    for node in nodes:
        display_text = node.label or f"{node.adnl[:4]}...{node.adnl[-4:]}"
        buttons.append([InlineKeyboardButton(text=display_text, callback_data=f"node:{node.id}")])

    buttons.append([InlineKeyboardButton(text="‹ Back", callback_data="main_menu")])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_text(text=TEXTS['my_nodes'], reply_markup=markup)


@edit_node_router.callback_query(lambda c: c.data.startswith('remove_node:'))
async def remove_node_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    await callback_query.answer()
    node_id = int(callback_query.data.split(':')[1])
    node = await db_manager.get_node_by_id(node_id)
    if not node or node.user_id != callback_query.from_user.id:
        await callback_query.answer("Node not found.")
        return
    await db_manager.remove_node(node_id)
    await callback_query.message.edit_text("Node has been successfully removed.")
    await asyncio.sleep(1)
    await my_nodes_callback_handler(callback_query, db_manager)


@edit_node_router.callback_query(lambda c: c.data.startswith('node:'))
async def node_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    node_id = int(callback_query.data.split(':')[1])

    node = await db_manager.get_node_by_id(node_id)

    if node and node.user_id == callback_query.from_user.id:  # Verify node belongs to this user
        await callback_query.answer()
        buttons = [
            # [InlineKeyboardButton(text="Edit Label", callback_data=f"edit_label:{node_id}")],
            [InlineKeyboardButton(text="Remove Node", callback_data=f"remove_node:{node_id}")],
            [InlineKeyboardButton(text="‹ Back", callback_data="my_nodes")]
        ]

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        node_text = f"Node: <b>{node.label or node.adnl[:10] + '...'}</b>\nADNL: <code>{node.adnl}</code>"
        await callback_query.message.edit_text(text=node_text, reply_markup=markup)
    else:
        await callback_query.answer("Node not found.")
