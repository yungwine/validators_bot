from typing import Optional


def amount_formatting(amount):
	return f"{amount:,}".replace(',', ' ')

def get_adnl_text(adnl_addr: str, label: Optional[str]):
	label_text = f" ({label})" if label else ''
	adnl_short = adnl_addr[:6] + "..." + adnl_addr[-6:]
	adnl_text = f"{adnl_short}{label_text}"
	return adnl_text
