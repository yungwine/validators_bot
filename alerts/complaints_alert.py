from alerts.alert import Alert
from alerts.toncenter import Toncenter
from database import Database, UserModel, NodeModel
from handlers import TEXTS
from utils import amount_formatting, get_adnl_text


class ComplaintsAlert(Alert):

	async def check(self, users: list[UserModel]) -> None:
		past_validation_cycle = await self.toncenter.get_validation_cycle(past=True)
		complaints = await self.toncenter.get_complaints_list(past_validation_cycle['cycle_id'])
		if not complaints:
			return
		for user in users:
			nodes = await self.database.get_user_nodes(user.user_id)
			nodes_dict = {n.adnl: n for n in nodes}
			if not nodes:
				continue
			for complaint in complaints:
				if complaint['is_passed'] is not True:
					continue
				if complaint['adnl_addr'] in nodes_dict:
					await self.warn(user, complaint, nodes_dict[complaint['adnl_addr']])

	async def warn(self, user: UserModel, complaint: dict, node: NodeModel):
		alert_name = f"{type(self).__name__}-{complaint['election_id']}-{complaint['adnl_addr']}"

		adnl_short = get_adnl_text(node.adnl, node.label)
		penalty = complaint['suggested_fine'] // 10**9  # todo: support fine_part
		text = TEXTS['complaint'].format(adnl=node.adnl, adnl_short=adnl_short, election_id=complaint['election_id'], penalty=amount_formatting(penalty))
		await self.inform(user, alert_name, text)
