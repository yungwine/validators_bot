import asyncio
import logging
import time
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command

from alerts.alert import ALERTS
from database import Database

admin_router = Router()

notification_data: Optional[str] = None
notification_task: Optional[asyncio.Task] = None


async def send_message_to_admins(bot, text: str, admin_users: list[int]) -> None:
    for admin_id in admin_users:
        await bot.send_message(chat_id=admin_id, text=text)


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

        for alert_type in ALERTS:
            users_with_alert = await db_manager.get_users_with_enabled_alert(alert_type, only_with_nodes=False)
            alert_counts[alert_type] = len(users_with_alert)

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


@admin_router.message(Command("add_notification"))
async def add_notification(message: types.Message, admin_users: list[int]) -> None:
    global notification_data

    if message.from_user.id not in admin_users:
        await message.answer("You are not authorized to use this command.")
        return
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer("Please provide notification text after the command.")
        return
    notification_data = command_parts[1]
    await message.answer("Notification stored. Use /print_notification to verify it or /start_notification to send.")


@admin_router.message(Command("print_notification"))
async def print_notification(message: types.Message, admin_users: list[int]) -> None:
    if message.from_user.id not in admin_users:
        await message.answer("You are not authorized to use this command.")
        return
    if notification_data is None:
        await message.answer("No notification is currently stored. Use /add_notification to add one.")
        return
    await message.answer(f"Current notification:\n\n{notification_data}")


@admin_router.message(Command("start_notification"))
async def start_notification(message: types.Message, db_manager: Database, admin_users: list[int]) -> None:
    global notification_task

    if message.from_user.id not in admin_users:
        await message.answer("You are not authorized to use this command.")
        return
    if notification_data is None:
        await message.answer("No notification is currently stored. Use /add_notification to add one.")
        return
    if notification_task is not None and not notification_task.done():
        await message.answer("A notification task is already in progress. Use /stop_notification to cancel it first.")
        return
    status_message = await message.answer("Notification will be sent in 60 seconds. Use /stop_notification to cancel.")
    notification_task = asyncio.create_task(
        send_notification_with_delay(message, db_manager, status_message, admin_users)
    )
    report_text = f"Notification sending started by @{message.from_user.username}.\n\nCheck the notification text with /print_notification or cancel it with /stop_notification."
    await send_message_to_admins(message.bot, report_text, admin_users)


@admin_router.message(Command("stop_notification"))
async def stop_notification(message: types.Message, admin_users: list[int]) -> None:
    global notification_task, notification_data

    if message.from_user.id not in admin_users:
        await message.answer("You are not authorized to use this command.")
        return
    if notification_task is None or notification_task.done():
        await message.answer("No notification task is currently running.")
        return
    notification_task.cancel()
    notification_task = None
    notification_data = None
    await send_message_to_admins(message.bot, "Notification task has been cancelled.", admin_users)


async def send_notification_with_delay(
        admin_message: types.Message,
        db_manager: Database,
        status_message: types.Message,
        admin_users: list[int]
) -> None:
    global notification_data
    try:
        await asyncio.sleep(60)

        await status_message.edit_text("Sending notification to all users...")

        all_users = await db_manager.get_users()
        total_users = len(all_users)
        successful = 0
        blocked = 0
        failed = 0

        start_time = time.time()

        for user in all_users:
            try:
                await admin_message.bot.send_message(
                    chat_id=user.user_id,
                    text=notification_data,
                    parse_mode="HTML"
                )
                successful += 1

                await asyncio.sleep(0.05)

            except Exception as e:
                error_message = str(e).lower()
                if "bot was blocked" in error_message:
                    blocked += 1
                else:
                    failed += 1
                logging.info(f"Failed to send notification to user {user.user_id}: {str(e)}")

        notification_data = None

        execution_time = time.time() - start_time
        stats_message = (
            "<b>📨 Notification Delivery Report:</b>\n\n"
            f"👥 Total Users: <code>{total_users}</code>\n"
            f"✅ Successfully Delivered: <code>{successful}</code>\n"
            f"🚫 Blocked by User: <code>{blocked}</code>\n"
            f"❌ Failed to Deliver: <code>{failed}</code>\n\n"
            f"⏱ Completed in <code>{execution_time:.2f}</code> sec"
        )
        await send_message_to_admins(admin_message.bot, stats_message, admin_users)

    except asyncio.CancelledError:
        logging.warning("Notification task cancelled.")
    except Exception as e:
        await admin_message.answer(f"<b>Error sending notification:</b>\n<code>{str(e)}</code>")
