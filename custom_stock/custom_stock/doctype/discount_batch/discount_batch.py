# -*- coding: utf-8 -*-
# Copyright (c) 2021, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class DiscountBatch(Document):
    pass


@frappe.whitelist()
def get_item_row(search_value):
    barcode = frappe.get_doc("Item Barcode", search_value)
    if(barcode):
        item = frappe.get_doc("Item", barcode.parent)
        return {
            "item_code": item.item_code,
            "item_name": item.item_name
        }
    return None
