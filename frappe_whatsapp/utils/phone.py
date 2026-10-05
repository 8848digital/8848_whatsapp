# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Phone number clean-up for WhatsApp recipients."""

import re

# Shortest / longest usable international number (E.164 allows 15 digits).
MIN_NUMBER_DIGITS = 10
MAX_NUMBER_DIGITS = 15


def format_number(number):
	"""
	Drop a leading "+" from a number, e.g. "+919876543210" -> "919876543210".

	Parameters:
		number (str, required): Phone number as typed.

	Returns:
		str: The number without the leading "+".
	"""
	if number.startswith("+"):
		number = number[1:]

	return number


def normalize_number(number, default_country_code=None):
	"""
	Reduce a number to the digits-only form Meta expects.

	Unlike format_number, this copes with the way numbers are typed into
	User and Employee records: spaces, dashes, brackets, a national trunk
	prefix, or no country code at all. Example: "098765 43210" with country
	code "+91" -> "919876543210".

	Parameters:
		number (str, required): Phone number as typed.
		default_country_code (str, optional): Added when the number has none.

	Returns:
		str | None: Digits-only number, or None when it can't be used, so the
		caller can skip and log the recipient instead of sending a request
		Meta will reject.
	"""
	if not number:
		return None

	digits = re.sub(r"\D", "", str(number))

	# Neither the international prefix nor the national trunk prefix is part
	# of the number Meta wants.
	if digits.startswith("00"):
		digits = digits[2:]
	elif digits.startswith("0"):
		digits = digits.lstrip("0")

	if len(digits) == MIN_NUMBER_DIGITS and default_country_code:
		country_code = re.sub(r"\D", "", str(default_country_code))
		digits = f"{country_code}{digits}"

	# A bare national number with no country code to add is not dialable.
	if len(digits) <= MIN_NUMBER_DIGITS or len(digits) > MAX_NUMBER_DIGITS:
		return None

	return digits
