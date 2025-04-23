import time

from alerts.alert import Alert
from alerts.utils import amount_formatting
from database import UserModel
from handlers.utils import TEXTS


class ComplaintsInformation(Alert):

	async def check(self, users: list[UserModel]):
		past_validation_cycle = await self.toncenter.get_validation_cycle(past=True)
		election_id = past_validation_cycle['cycle_id']
		utime_until = past_validation_cycle['cycle_info']['utime_until']
		if time.time() < utime_until + 1200:
			return

		complaints_list = await self.toncenter.get_complaints_list(election_id)
		complaints = []
		for complaint in complaints_list:
			if complaint['is_passed'] is not True:
				continue
			complaints.append(complaint)
		complaints.reverse()

		complaints_text = ''
		for complaint in complaints:
			penalty = complaint.suggested_fine // 10**9
			penalty_text = amount_formatting(penalty)
			validator = await self.toncenter.get_validator(complaint.adnl_addr, past=True)
			efficiency = await self.toncenter.get_validator_efficiency(complaint.adnl_addr, election_id)
			complaints_text += TEXTS['complaint'].format(index=validator['index'], adnl=complaint['adnl_addr'],
														 efficiency=efficiency, penalty=penalty_text)
			complaints_text += '\n'

		start_time = timestamp2utcdatetime(election_id)
		end_time = timestamp2utcdatetime(utime_until)
		inform_text = TEXTS["complaints_information"].format(election_id=election_id, start_time=start_time, end_time=end_time, complaints=complaints_text)

		alert_name = f"{type(self).__name__}-{election_id}"

		for user in users:
			await self.inform(user, alert_name, inform_text)

def timestamp2utcdatetime(timestamp, format="%d.%m.%Y %H:%M:%S"):
	datetime = time.gmtime(timestamp)
	result = time.strftime(format, datetime) + ' UTC'
	return result
