from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import Database
from handlers.utils import TEXTS
from alerts.alert import ALERTS

notifications_router = Router(name=__name__)


@notifications_router.callback_query(lambda c: c.data == 'notifications')
async def my_nodes_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    await callback_query.answer()
    user_alerts = await db_manager.get_user_alerts(callback_query.from_user.id)
    enabled_alerts = []
    for alert in user_alerts:
        if alert.enabled:
            enabled_alerts.append(alert.alert_type)
    text = TEXTS['my_alerts'].format(alerts=', '.join(enabled_alerts))
    buttons = []

    for alert in ALERTS:
        if alert.type in enabled_alerts:
            buttons.append([InlineKeyboardButton(text=f"Disable {alert.name}", callback_data=f"alert:disable:{alert.type}")])
        else:
            buttons.append([InlineKeyboardButton(text=f"Enable {alert.name}", callback_data=f"alert:enable:{alert.type}")])

    buttons.append([InlineKeyboardButton(text="‹ Back", callback_data="main_menu")])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.edit_text(text=text, reply_markup=markup)


@notifications_router.callback_query(lambda c: c.data.startswith('alert:'))
async def alert_callback_handler(callback_query: CallbackQuery, db_manager: Database) -> None:
    await callback_query.answer()

    buttons = [[InlineKeyboardButton(text="‹ Back", callback_data="notifications")]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    action, alert_id = callback_query.data.split(':')[1:]
    if action == 'enable':
        await db_manager.set_user_alert_enabled(callback_query.from_user.id, alert_id, True)
        await callback_query.message.edit_text(text=TEXTS['alert_enabled'].format(alert=alert_id), reply_markup=markup)
    elif action == 'disable':
        await db_manager.set_user_alert_enabled(callback_query.from_user.id, alert_id, False)
        await callback_query.message.edit_text(text=TEXTS['alert_disabled'].format(alert=alert_id), reply_markup=markup)
    elif action == 'disable_no_edit':
        await db_manager.set_user_alert_enabled(callback_query.from_user.id, alert_id, False)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer(text=TEXTS['alert_disabled'].format(alert=alert_id))
