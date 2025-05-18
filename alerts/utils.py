from typing import Optional


def amount_formatting(amount):
	return f"{amount:,}".replace(',', ' ')

def get_adnl_text(adnl_addr: str, label: Optional[str], cut: bool = True):
	label_text = f" ({label})" if label else ''
	if cut:
		adnl_text = adnl_addr[:6] + "..." + adnl_addr[-6:] + label_text
	else:
		adnl_text = adnl_addr + label_text
	return adnl_text
