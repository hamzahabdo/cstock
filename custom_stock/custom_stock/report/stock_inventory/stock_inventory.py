# Copyright (c) 2013, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_data(filters):
    conditions, filters = get_conditions(filters)
    query = '''
		SELECT item_code, item_name, item_group, inventory_qty, actual_qty, difference_qty, rate, amount
		FROM `tabStock Inventory Processing Item`
		WHERE docstatus = 1 %s
	'''
    siis = frappe.db.sql(query % conditions, filters, as_dict=1)
    data = []
    for sii in siis:
        row = [sii.item_code, sii.item_name, sii.item_group,
               sii.inventory_qty, sii.actual_qty, sii.difference_qty, sii.rate, sii.amount]

        data.append(row)
    return data


def get_conditions(filters):
    conditions = ""
    # print(type(filters.get("inventory_type")))
    if filters.get("inventory_type"):
        # if len(filters.get("inventory_type")) > 1:
        #     connector = " or "
        # else:
        # connector = " and ("
        conditions += " and ("  # connector
        l = len(filters.get("inventory_type"))
        for it in filters.get("inventory_type"):
            l = l - 1
            if it == _("Deficit"):
                conditions += "(difference_qty < 0  and inventory_qty != 0)"
            if it == _("Surplus"):
                conditions += "difference_qty > 0"
            if it == _("Uninventorized"):
                conditions += "inventory_qty = 0"
            if l != 0:
                conditions += " or "
            else:
                conditions += ")"

    if filters.get("inventory_voucher"):
        conditions += " and parent = %(inventory_voucher)s"
    if filters.get("item_group"):
        conditions += " and item_group in %(item_group)s"
    if filters.get("not_in_item_group"):
        conditions += " and item_group not in %(not_in_item_group)s"

    return conditions, filters


def get_columns(filters):
    columns = [
        _("Item") + ":Link/Item:250",
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "width": 200,
            "hidden": 1
        },
        _("Item Group") + ":Link/Item Group:200",
        _("Inventory Quantity") + "::100",
        _("Actual Quantity") + "::100",
        _("Difference Quantity") + "::100",
        _("Rate") + ":Currency:100",
        _("Amount") + ":Currency:100"
    ]

    return columns
