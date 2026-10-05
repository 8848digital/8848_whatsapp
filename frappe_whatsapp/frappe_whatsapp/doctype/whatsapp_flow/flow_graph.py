# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Low-level Graph API reads for WhatsApp Flows."""

import frappe
import requests

from frappe_whatsapp.utils.meta_api import get_graph_url


def get_flow_details(account_name, flow_id, fields):
	"""
	GET a flow's details from the Graph API.

	Parameters:
		account_name (str, required): WhatsApp Account name.
		flow_id (str, required): WhatsApp flow id.
		fields (str, required): Comma-separated fields to request.

	Returns:
		dict: Flow details.
	"""
	account, headers = get_flow_api(account_name)
	response = requests.get(get_graph_url(account, f"{flow_id}?fields={fields}"), headers=headers)
	response.raise_for_status()
	return response.json()


def fetch_flow_json(account_name, flow_id):
	"""
	Download the flow's "flow.json" asset; failures are logged, not raised.

	Parameters:
		account_name (str, required): WhatsApp Account name.
		flow_id (str, required): WhatsApp flow id.

	Returns:
		dict | None: The Flow JSON.
	"""
	account, headers = get_flow_api(account_name)
	try:
		response = requests.get(get_graph_url(account, f"{flow_id}/assets"), headers=headers)
		response.raise_for_status()

		for asset in response.json().get("data", []):
			if asset.get("name") != "flow.json" or not asset.get("download_url"):
				continue
			asset_response = requests.get(asset["download_url"], headers=headers)
			if asset_response.status_code == 200:
				return asset_response.json()

		return None
	except Exception as e:
		frappe.log_error(f"Failed to fetch flow JSON: {str(e)}")
		return None


def get_flow_api(account_name):
	"""
	The WhatsApp Account and its bearer header for Flow API calls.

	Parameters:
		account_name (str, required): WhatsApp Account name.

	Returns:
		tuple: (account Document, {"Authorization": "Bearer ..."})
	"""
	account = frappe.get_doc("WhatsApp Account", account_name)
	return account, {"Authorization": f"Bearer {account.get_password('token')}"}
