# Copyright (c) 2013, burjalmaha.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters):
    columns = []
    if(filters.group_by == "Item"):
        columns.extend([
            {"label": _("Item"), "fieldname": "item_code",
             "fieldtype": "Link", "options": "Item"},
            {"label": _("Item Name"), "fieldname": "item_name"},
            {"label": _("Item Group"), "fieldname": "item_group",
             "fieldtype": "Link", "options": "Item Group"},
            {"label": _("Supplier"), "fieldname": "n_supplier",
             "fieldtype": "Link", "options": "Supplier"}
        ])
    elif(filters.group_by == "Item Group"):
        columns.append({"label": _("Item Group"), "fieldname": "item_group",
                        "fieldtype": "Link", "options": "Item Group"})
    elif(filters.group_by == "Supplier"):
        columns.append({"label": _("Supplier"), "fieldname": "n_supplier",
                        "fieldtype": "Link", "options": "Supplier"})
    columns.extend([
        {"label": _("Quantity"), "fieldname": "actual_qty",
         "fieldtype": "Float"},
        {"label": _("Valuation"), "fieldname": "valuation",
         "fieldtype": "Float"},
        {"label": _("Sales Price"), "fieldname": "price",
         "fieldtype": "Float"}
    ])
    return columns


def get_data(filters):
    sle = get_stock_ledger_entries(filters)
    item_map = get_item_map(sle)
    data = []
    item_details = get_item_details(
        filters, "','".join(i for i in item_map.keys()))
    for key, value in item_map.items():
        data.append({
            "item_code": key,
            "actual_qty": value["bal_qty"],
            "valuation": value["bal_val"],
            "item_name": item_details[key]["item_name"],
            "item_group": item_details[key]["item_group"],
            "n_supplier": item_details[key]["n_supplier"],
            "price": value["bal_qty"] * (item_details[key]["price"] or 0)
        })
    return group_date(data, filters)


def group_date(data, filters):
    grouped_data = []
    if(filters.group_by == "Item"):
        grouped_data = data
    elif(filters.group_by == "Item Group"):
        for g in frappe.get_list("Item Group"):
            actual_qty = valuation = price = 0
            for d in data:
                if(d["item_group"] == g.name):
                    actual_qty += d["actual_qty"]
                    valuation += d["valuation"]
                    price += d["price"] or 0
            if(actual_qty > 0):
                grouped_data.append(
                    {
                        "item_group": g.name,
                        "actual_qty": actual_qty,
                        "valuation": valuation,
                        "price": price
                    })
    elif(filters.group_by == "Supplier"):
        for s in frappe.get_list("Supplier"):
            actual_qty = valuation = price = 0
            for d in data:
                if(d["n_supplier"] == s.name):
                    actual_qty += d["actual_qty"]
                    valuation += d["valuation"]
                    price += d["price"] or 0
            if(actual_qty > 0):
                grouped_data.append(
                    {
                        "n_supplier": s.name,
                        "actual_qty": actual_qty,
                        "valuation": valuation,
                        "price": price
                    })
    return grouped_data


def get_stock_ledger_entries(filters):
    return frappe.db.sql("""
        select
            sle.item_code, sle.actual_qty, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference
        from
            `tabStock Ledger Entry` sle
        where sle.docstatus < 2
        and sle.warehouse = '{}'
        and sle.posting_date <= '{}'
        order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty""".format(filters.warehouse, filters.to_date), as_dict=1)


def get_item_map(sle):
    item_map = {}
    for d in sle:
        if d.item_code not in item_map:
            item_map[d.item_code] = frappe._dict({
                "bal_qty": 0.0, "bal_val": 0.0
            })
        qty_dict = item_map[d.item_code]
        if d.voucher_type == "Stock Reconciliation":
            qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
        else:
            qty_diff = flt(d.actual_qty)
        qty_dict.bal_qty += qty_diff
        qty_dict.bal_val += flt(d.stock_value_difference)
    return item_map


def get_item_details(filters, items):
    item_details = {}

    if not items:
        return item_details

    sql = """
        select
            item.name, item.item_name, item.item_group, item.n_supplier,
            (
            select p.price_list_rate
            from `tabItem Price` p
            where p.item_code = item.name
            and p.price_list = '{}'
            and p.valid_from <= '{}'
            order by p.valid_from desc
            limit 1
            ) as price
        from
            `tabItem` item
        where
            item.name in ('{}')
    """.format(filters.price_list, filters.to_date, items)
    res = frappe.db.sql(sql, as_dict=1)

    for item in res:
        item_details.setdefault(item.name, item)

    return item_details
