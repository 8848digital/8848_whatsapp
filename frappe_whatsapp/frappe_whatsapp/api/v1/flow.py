# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
# Copyright (c) 2026, Shridhar Patil and contributors
# For license information, please see license.txt

"""Endpoints behind the WhatsApp Flow form and list buttons."""

import frappe

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow import flow_import
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_flow.flow_meta import load_flow


@frappe.whitelist(methods=["POST"])
def create_on_whatsapp(flow: str):
	"""
	Create a WhatsApp Flow on Meta and upload its Flow JSON.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.create_on_whatsapp`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	load_flow(flow).create_on_whatsapp()


@frappe.whitelist(methods=["POST"])
def upload_flow_json(flow: str):
	"""
	Upload the flow's current screens and fields to Meta as its Flow JSON.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.upload_flow_json`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	load_flow(flow).upload_flow_json()


@frappe.whitelist(methods=["POST"])
def publish_flow(flow: str):
	"""
	Publish a flow so it can be sent to customers.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.publish_flow`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	load_flow(flow).publish_flow()


@frappe.whitelist(methods=["POST"])
def deprecate_flow(flow: str):
	"""
	Deprecate a published flow so it can no longer be sent.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.deprecate_flow`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	load_flow(flow).deprecate_flow()


@frappe.whitelist(methods=["POST"])
def delete_from_whatsapp(flow: str):
	"""
	Delete a flow on Meta and turn the local one back into a draft.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.delete_from_whatsapp`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": null, "errors": null}
```
	"""
	load_flow(flow).delete_from_whatsapp()


@frappe.whitelist()
def get_flow_preview(flow: str):
	"""
	Get the web preview link for a flow.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.get_flow_preview`
	**HTTP Method:** GET, POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": "https://business.facebook.com/wa/manage/flows/.../preview/...", "errors": null}
```
	"""
	return load_flow(flow).get_flow_preview()


@frappe.whitelist(methods=["POST"])
def send_test(flow: str, phone_number: str, message: str | None = None):
	"""
	Send a flow to a phone number to try it; draft flows only reach test numbers.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.send_test`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
		- phone_number (str, required): Recipient number with country code
		- message (str, optional): Text shown above the flow button
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": "WA-MSG-0001", "errors": null}
```
	"""
	return load_flow(flow).send_test(phone_number, message)


@frappe.whitelist()
def get_flow_status(flow: str):
	"""
	Read a flow's status and validation errors from Meta.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.get_flow_status`
	**HTTP Method:** GET, POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": {"id": "123", "status": "DRAFT", "validation_errors": []}, "errors": null}
```
	"""
	return load_flow(flow).get_flow_status()


@frappe.whitelist(methods=["POST"])
def sync_from_whatsapp(flow: str):
	"""
	Copy a flow's status, category, preview link and Flow JSON from Meta.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.sync_from_whatsapp`
	**HTTP Method:** POST
	**Parameters:**
		- flow (str, required): WhatsApp Flow name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": {"id": "123", "status": "PUBLISHED"}, "errors": null}
```
	"""
	return load_flow(flow).sync_from_whatsapp()


@frappe.whitelist()
def get_whatsapp_flows(whatsapp_account: str):
	"""
	List the flows of a WhatsApp Business Account, marking those already imported.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.get_whatsapp_flows`
	**HTTP Method:** GET, POST
	**Parameters:**
		- whatsapp_account (str, required): WhatsApp Account name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": [{"id": "123", "name": "Lead form", "status": "PUBLISHED", "exists_locally": false, "local_name": null}], "errors": null}
```
	"""
	return flow_import.list_meta_flows(whatsapp_account)


@frappe.whitelist(methods=["POST"])
def import_flow_from_whatsapp(whatsapp_account: str, flow_id: str, flow_name: str | None = None):
	"""
	Import a flow from Meta, with its screens and fields, as a new WhatsApp Flow.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.import_flow_from_whatsapp`
	**HTTP Method:** POST
	**Parameters:**
		- whatsapp_account (str, required): WhatsApp Account name
		- flow_id (str, required): Flow id on WhatsApp
		- flow_name (str, optional): Local name; defaults to the name on WhatsApp
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": "Lead form", "errors": null}
```
	"""
	return flow_import.import_flow(whatsapp_account, flow_id, flow_name)


@frappe.whitelist(methods=["POST"])
def sync_all_flows(whatsapp_account: str):
	"""
	Import new flows from Meta and refresh the ones already here.

	**Endpoint:** `/api/method/frappe_whatsapp.frappe_whatsapp.api.v1.flow.sync_all_flows`
	**HTTP Method:** POST
	**Parameters:**
		- whatsapp_account (str, required): WhatsApp Account name
	**Response:**
```json
		{"status": true, "status_code": 200, "message": "Request processed successfully", "data": {"imported": 2, "updated": 1, "skipped": 0}, "errors": null}
```
	"""
	return flow_import.sync_all_flows(whatsapp_account)
