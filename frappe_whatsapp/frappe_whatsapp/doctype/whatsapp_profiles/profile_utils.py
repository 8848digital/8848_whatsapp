# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Clean-up for WhatsApp Profiles."""

from frappe_whatsapp.utils.phone import format_number


def clean_profile(profile):
	"""
	Store the number without "+" and set the title to "<name> - <number>".

	Parameters:
		profile (Document, required): WhatsApp Profiles record.

	Returns:
		None
	"""
	if profile.number:
		profile.number = format_number(profile.number)

	title_parts = [part for part in (profile.profile_name, profile.number) if part]
	profile.title = " - ".join(title_parts) or "Unnamed Profile"
