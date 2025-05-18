from alerts.alert import Alert
from database import UserModel, NodeModel
from handlers.utils import TEXTS
from alerts.utils import amount_formatting, get_adnl_text


class ElectionsInformation(Alert):

	disable_notification = True

	async def check(self, users: list[UserModel]):
		election_data = await self.toncenter.get_election_data()
		elections_data_dict = {p['adnl_addr']: p for p in election_data['participants_list']}
		for user in users:
			user_nodes = await self.database.get_user_nodes(user.user_id)
			user_participants = get_sorted_participants(elections_data_dict, user_nodes)
			if not election_data['finished']:
				await self.check_before_start(election_data['election_id'], user, user_participants)
			else:
				await self.check_after_start(election_data['election_id'], user, user_nodes, user_participants)

	async def check_before_start(self, election_id: int, user: UserModel, user_participants_list: dict):
		for node_election_data, node in user_participants_list.values():
			await self.inform_before_start(user, election_id, node, node_election_data)

	async def inform_before_start(self, user: UserModel, election_id, node: NodeModel, node_data: dict):
		alert_name = f"{type(self).__name__}-{election_id}-{node.adnl}"
		adnl_text = get_adnl_text(node.adnl, node.label, cut=False)
		stake = node_data['stake'] // 10**9
		text = TEXTS['stake_sent'].format(adnl=adnl_text, stake=amount_formatting(stake))
		await self.inform(user, alert_name, text)

	async def check_after_start(self, election_id: int, user: UserModel, user_nodes: list[NodeModel], user_participants: dict):
		problem_nodes = []
		for node in user_nodes:
			if node.adnl in user_participants:
				continue
			problem_nodes.append(node)
		if not len(problem_nodes):
			return
		await self.inform_after_start(user, election_id, problem_nodes)

	async def inform_after_start(self, user: UserModel, election_id: int, problem_nodes: list[NodeModel]):
		alert_name = f"{type(self).__name__}-{election_id}"
		text = TEXTS['stake_not_sent'].format(election_id=election_id)
		for node in problem_nodes:
			adnl_text = get_adnl_text(node.adnl, node.label, cut=False)
			text += f"<code>{adnl_text}</code>\n"
		await self.inform(user, alert_name, text)


def get_sorted_participants(election_data_dict, node_list):
	result = {}
	for node in node_list:
		if node.adnl not in election_data_dict:
			continue
		result[node.adnl] = (election_data_dict[node.adnl], node)
	# for participant in election_data['participants_list']:
	# 	if participant['adnl_addr'] not in adnl_list:
	# 		continue
	# 	result[participant['adnl_addr']] = participant
	return result
