import asyncio
import time
from typing import Optional

import aiohttp


async def try_get_url(url, timeout=30):
	attempts = 3
	async with aiohttp.ClientSession() as session:
		for attempt in range(attempts):
			try:
				async with session.get(url, timeout=timeout) as response:
					if response.status == 200:
						return await response.json()
					response.raise_for_status()
			except (aiohttp.ClientError, asyncio.TimeoutError) as e:
				if attempt < attempts - 1:
					await asyncio.sleep(1)
				else:
					raise
	raise Exception(f"Failed to fetch URL after {attempts} attempts: {url}: {e}")


class Toncenter:
	def __init__(self, api_key: str):
		self.api_key = api_key

	async def get_validator_efficiency(self, adnl, election_id):
		efficiency_list = await self.get_efficiency_list(election_id=election_id)
		for validator in efficiency_list:
			if validator['adnl_addr'] == adnl:
				efficiency = round(validator.efficiency, 2)
				return efficiency

	async def get_validator(self, adnl, past=False):
		validators = await self.get_validators(past=past)
		for validator in validators:
			if validator['adnl_addr'] == adnl:
				return validator

	async def get_validators_list(self):
		result = list()
		validators = await self.get_validators()
		for item in validators:
			adnl_addr = item.get("adnl_addr")
			if adnl_addr:
				result.append(adnl_addr)
		return result

	async def is_send_telemetry(self, adnl: str) -> bool:
		node = await self.get_telemetry_for_adnl(adnl)
		if node:
			return True
		return False

	async def get_validation_cycle(self, past=False):
		data = await self.get_validation_cycles_list()
		if past:
			return data[1]
		else:
			return data[0]

	async def get_validators(self, past=False):
		data = await self.get_validation_cycle(past=past)
		return data['cycle_info']['validators']

	async def get_election_data(self):
		data = await self.get_elections_list()
		return data[0]

	async def get_telemetry_for_adnl(self, adnl: str) -> Optional[dict]:
		timestamp = int(time.time())
		url = f"https://telemetry.toncenter.com/getTelemetryData?timestamp_from={timestamp-100}&api_key={self.api_key}&adnl_address={adnl}"
		data = await try_get_url(url)
		if data:
			return data[0]
		return None

	async def get_telemetry_list(self) -> list:
		timestamp = int(time.time())
		url = f"https://telemetry.toncenter.com/getTelemetryData?timestamp_from={timestamp-100}&api_key={self.api_key}"
		data = await try_get_url(url)
		return data

	async def get_validation_cycles_list(self) -> list:
		url = "https://elections.toncenter.com/getValidationCycles?limit=2"
		data = await try_get_url(url)
		return data

	async def get_elections_list(self) -> list:
		url = "https://elections.toncenter.com/getElections"
		data = await try_get_url(url)
		return data

	async def get_complaints_list(self, election_id) -> list:
		url = f"https://elections.toncenter.com/getComplaints?election_id={election_id}&limit=100"
		data = await try_get_url(url)
		return data

	async def get_efficiency_list(self, election_id) -> list:
		url = f"https://toncenter.com/api/qos/cycleScoreboard?cycle_id={election_id}&limit=1000"
		data = await try_get_url(url)
		return data['scoreboard']
