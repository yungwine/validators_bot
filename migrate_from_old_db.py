import argparse
import asyncio
import time

from database import Database
import json

# new_db_path = sqlite+aiosqlite:///bot_users.db


async def migrate():
    new_db = Database(new_db_path)
    await new_db.init_db()

    for user_id_str, user_data in old_db['users'].items():
        user_id = int(user_id_str)
        await new_db.add_user_with_alerts(user_id, None)

        for adnl in user_data['adnl_list']:
            label = user_data.get('labels', {}).get(adnl)
            await new_db.add_node(user_id, adnl, label)

        for alert_type in user_data.get('disable_alerts_list', []):
            await new_db.set_user_alert_enabled(user_id, alert_type, False)

        for alert_name, timestamp in user_data.get('triggered_alerts_list', {}).items():
            if timestamp < time.time() - 86400:
                continue
            await new_db.add_triggered_alert(user_id, alert_name, timestamp)

    print(f"Migration completed: {len(old_db['users'])} users migrated")


if __name__ == "__main__":
    if input('Continue?') != 'y':
        exit(1)

    parser = argparse.ArgumentParser(description="Migrate from old JSON DB to new SQLite DB")
    parser.add_argument('--old_db_path', help="Path to the old JSON database file")
    parser.add_argument('--new_db_path', default='sqlite+aiosqlite:///bot_users.db',
                        help="Database URL for the new database")

    args = parser.parse_args()

    old_db_path, new_db_path = args.old_db_path, args.new_db_path

    with open(old_db_path) as f:
        old_db = json.load(f)

    asyncio.run(migrate())
