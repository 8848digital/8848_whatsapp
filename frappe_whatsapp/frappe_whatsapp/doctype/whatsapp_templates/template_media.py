# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Upload a template header's sample image or document to Meta for approval."""

import frappe
import magic
import requests
from frappe.integrations.utils import make_post_request

from frappe_whatsapp.utils.meta_api import get_auth_headers, get_graph_url


def upload_sample_media(template):
	"""
	Upload the header's sample image/document to Meta (resumable upload API).

	Meta needs a sample to approve a media header. The returned handle is
	kept on template.flags.media_handle for build_header.

	Parameters:
		template (Document, required): WhatsApp Templates record with "sample" set.

	Returns:
		None
	"""
	account = frappe.get_doc("WhatsApp Account", template.whatsapp_account)
	file_content, file_type = read_sample_file(template.sample)

	session = make_post_request(
		get_graph_url(account, f"{account.app_id}/uploads"),
		headers=get_auth_headers(account),
		data={"file_length": len(file_content), "file_type": file_type, "messaging_product": "whatsapp"},
	)

	upload = make_post_request(
		get_graph_url(account, session["id"]),
		headers={"authorization": f"OAuth {account.get_password('token')}"},
		data=file_content,
	)
	template.flags.media_handle = upload["h"]


def read_sample_file(file_url):
	"""
	Content and MIME type of a sample file, from a URL or from this site's files.

	Parameters:
		file_url (str, required): Full URL or a site path like "/files/sample.png".

	Returns:
		tuple: (bytes content, str MIME type)
	"""
	if file_url.startswith(("http://", "https://")):
		try:
			response = requests.get(file_url, timeout=30)
			response.raise_for_status()
		except Exception as e:
			frappe.throw(f"Failed to download file from URL: {str(e)}")

		content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
		return response.content, content_type or get_mime_type(response.content)

	# Read through File so the path is resolved by Frappe; never open() a raw URL.
	content = frappe.get_doc("File", {"file_url": file_url}).get_content()
	return content, get_mime_type(content)


def get_mime_type(content):
	"""
	Detect a file's MIME type from its bytes.

	Parameters:
		content (bytes, required): File content.

	Returns:
		str: e.g. "image/png".
	"""
	return magic.Magic(mime=True).from_buffer(content)
