import asyncio
import os

from alerts.alert import Alert
from alerts.utils import amount_formatting, get_adnl_text
from database import UserModel, NodeModel
from handlers.utils import TEXTS


class TelemetryAlert(Alert):

	async def check(self, users: list[UserModel]):
		for user in users:
			nodes = await self.database.get_user_nodes(user.user_id)
			for node in nodes:
				node_telemetry = await self.toncenter.get_telemetry(node.adnl)
				if node is None:
					continue
				tasks = [
					self.check_sync(user, node_telemetry, node),
					self.check_cpu(user, node_telemetry, node),
					self.check_ram(user, node_telemetry, node),
					self.check_network(user, node_telemetry, node),
					self.check_disk(user, node_telemetry, node),
				]
				res = await asyncio.gather(*tasks, return_exceptions=True)
				for r in res:
					if isinstance(r, Exception):
						self.logger.error(r)

	async def check_sync(self, user: UserModel, node_data: dict, node: NodeModel):
		out_of_sync = node_data['validatorStatus']['out_of_sync']
		await self.check_with_threshold(user, alert_name="Sync", node=node, value=out_of_sync,
										upper=40, lower=20)

	async def check_cpu(self, user: UserModel, node_data: dict, node: NodeModel):
		cpu_load = node_data['data']['cpuLoad'][2]
		cpu_number = node_data['data']['cpuNumber']
		value_percent = round(cpu_load / cpu_number * 100, 2)
		await self.check_with_threshold(user, alert_name="CPU", node=node, value=value_percent,
								  upper=90, lower=85, value_cpu_load=cpu_load,
								  value_percent=value_percent, cpu_load_max=cpu_number)

	async def check_ram(self, user: UserModel, node_data: dict, node: NodeModel):
		memory_usage = node_data['data']['memory']['usage']
		memory_total = node_data['data']['memory']['total']
		value_percent = round(memory_usage / memory_total * 100, 2)
		await self.check_with_threshold(user, alert_name="RAM", node=node, value=value_percent,
								  upper=90, lower=85, value_ram=memory_usage, ram_max=memory_total)

	async def check_network(self, user: UserModel, node_data: dict, node: NodeModel):
		network_load = node_data['data']['netLoad'][2]
		await self.check_with_threshold(user, alert_name="Network", node=node, value=network_load,
								  upper=500, lower=450)

	async def check_disk(self, user: UserModel, node_data: dict, node: NodeModel):
		disk_name = os.path.basename(node_data['data']['validatorDiskName'])
		if disk_name not in node_data['data']['disksLoad']:
			disk_name = list(node_data['data']['disksLoad'].keys())[0]
		disk_load = node_data['data']['disksLoad'][disk_name][2]
		disk_load_percent = node_data['data']['disksLoadPercent'][disk_name][2]
		await self.check_with_threshold(user, alert_name="Disk", node=node, value=disk_load_percent,
								  upper=90, lower=80, value_load=disk_load)

	async def check_with_threshold(self, user: UserModel, alert_name: str, node: NodeModel, upper: int, lower: int, value: int, **kwargs):
		if value > upper:
			await self.warn(user, alert_name, node=node, overloaded=True, threshold=upper, **kwargs)
		elif value < lower:
			await self.warn(user, alert_name, node=node, overloaded=False, threshold=lower, **kwargs)

	async def warn(self, user: UserModel, alert_type: str, overloaded: bool, node: NodeModel, **kwargs):
		alert_name = f"{type(self).__name__}-{alert_type}-{node.adnl}"
		adnl_short = get_adnl_text(node.adnl, node.label)
		overloaded_str = "_overloaded" if overloaded else "_ok"
		text_name = alert_type.lower() + overloaded_str
		text = TEXTS[text_name].format(adnl_short=adnl_short, adnl=node.adnl, **kwargs)
		await self.inform(user, alert_name, text, overloaded)

	async def inform(self, user: UserModel, alert_name: str, text: str, overloaded: bool):
		triggered_alerts = await self.database.get_triggered_alerts(user.user_id, alert_name)
		if bool(triggered_alerts) == overloaded:
			return
		await self.send_message(user.user_id, text)
		if overloaded:
			await self.database.add_triggered_alert(user.user_id, alert_name)
		else:
			await self.database.delete_triggered_alert(user.user_id, alert_name)
		self.logger.info(f"Sent alert {alert_name} to user {user.user_id}")
