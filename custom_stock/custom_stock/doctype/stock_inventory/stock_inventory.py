# -*- coding: utf-8 -*-
# Copyright (c) 2020, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint
from frappe.model.mapper import get_mapped_doc


class StockInventory(Document):
    pass


@frappe.whitelist()
def search_serial_or_batch_or_barcode_number_or_item_code(search_value):
    # search barcode no
    barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, [
                                       'barcode', 'parent as item_code'], as_dict=True)
    if barcode_data:
        return barcode_data

    # search item_code
    item_code_data = frappe.db.get_value('Item', {'item_code': search_value}, [
                                         'item_code', 'item_code'], as_dict=True)
    if item_code_data:
        return item_code_data

    return {}


@frappe.whitelist()
def get_list_of_item_codes_based_on_list_of_barcodes(barcode_list):
    barcode_list = barcode_list.split(",")
    return frappe.db.get_list('Item Barcode', {'barcode': ['in', barcode_list]}, ['parent as item_code'])


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
    args = frappe.parse_json(target_doc)
    if args.purpose == "Material Receipt":
        qtys = 1
        def condition(doc): return doc.difference_qty > 0
    elif args.purpose == "Material Issue":
        qtys = -1
        def condition(doc): return doc.difference_qty < 0
    else:
        qtys = 0

    def update_item(obj, target, source_parent):
        qty = flt(obj.difference_qty * qtys)
        target.qty = qty
        target.conversion_factor = 1
        target.transfer_qty = qty * target.conversion_factor
        # frappe.get_value('Item', obj.item_code, 'stock_uom')
        target.uom = target.stock_uom

        if qtys > 0:
            target.t_warehouse = source_parent.warehouse
        else:
            target.s_warehouse = source_parent.warehouse

    def set_missing_values(source, target):
        target.run_method("calculate_rate_and_amount")
        target.set_stock_entry_type()
        target.set_job_card_data()

    doc = get_mapped_doc("Stock Inventory Processing", source_name, {
        "Stock Inventory Processing": {
            "doctype": "Stock Entry",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Stock Inventory Processing Item": {
            "doctype": "Stock Entry Detail",
            "field_map": {
                "difference_qty": "transfer_qty",
                "difference_qty": "qty",
            },
            "postprocess": update_item,
            "condition": condition
        }
    }, target_doc, set_missing_values)

    return doc
