import time

from aiogram import Router, types
from aiogram.filters import Command

from alerts.alert import ALERTS
from database import Database

admin_router = Router()


@admin_router.message(Command("stats"))
async def get_user_stats(message: types.Message, db_manager: Database, admin_users: list[int]) -> None:
    if not message.from_user.id in admin_users:
        await message.answer("You are not authorized to use this command.")
        return

    try:
        start_time = time.time()

        all_users = await db_manager.get_users()
        total_users = len(all_users)

        total_nodes = 0
        users_with_nodes = 0
        all_adnls = []

        for user in all_users:
            user_nodes = await db_manager.get_user_nodes(user.user_id)
            if user_nodes:
                users_with_nodes += 1
                total_nodes += len(user_nodes)
                for node in user_nodes:
                    all_adnls.append(node.adnl)

        unique_adnls = len(set(all_adnls))

        alert_counts = {}

        for alert in ALERTS:
            users_with_alert = await db_manager.get_users_with_enabled_alert(alert.type, only_with_nodes=False)
            alert_counts[alert.type] = len(users_with_alert)

        execution_time = time.time() - start_time

        alert_stats = "\n".join([f"  {alert_type}: {count}" for alert_type, count in alert_counts.items()])

        stats_message = (
            "<b>📊 User Statistics:</b>\n\n"
            f"👥 Total Users: <code>{total_users}</code>\n"
            f"👤 Active Users (with nodes): <code>{users_with_nodes}</code>\n"
            f"🖥 Total ADNLs: <code>{total_nodes}</code>\n"
            f"🔄 Unique ADNLs: <code>{unique_adnls}</code>\n"
            f"🔔 Enabled Alerts: \n<code>{alert_stats}</code>\n\n"
            f"⏱ Stats fetched in <code>{execution_time:.3f}</code> sec"
        )

        await message.answer(stats_message)
    except Exception as e:
        await message.answer(f"<b>Error getting statistics:</b>\n<code>{str(e)}</code>")
