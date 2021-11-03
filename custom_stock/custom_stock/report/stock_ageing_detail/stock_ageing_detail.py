# Copyright (c) 2013, burjalmaha.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now, date_diff
from erpnext.stock.utils import add_additional_uom_columns
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition

from six import iteritems


def execute(filters=None):
    if not filters:
        filters = {}

    validate_filters(filters)

    columns = get_columns(filters)
    items = get_items(filters)
    sle = get_stock_ledger_entries(filters, items)

    # if no stock ledger entry found return
    if not sle:
        return columns, []

    iwb_map = get_item_warehouse_map(filters, sle)
    item_map = get_item_details(items, sle, filters)

    data = []

    def _func(x): return x[1]

    for (company, item, warehouse) in sorted(iwb_map):
        if item_map.get(item):
            qty_dict = iwb_map[(company, item, warehouse)]

            report_data = {
                'item_code': item,
                'warehouse': warehouse,
                'company': company
            }
            report_data.update(item_map[item])
            report_data.update(qty_dict)

            if(report_data["bal_qty"] != 0):
                data.append(report_data)

    return columns, data


def get_columns(filters):
    """return columns"""

    columns = [
        {"label": _("Item"), "fieldname": "item_code",
         "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Item Name"), "fieldname": "item_name", "width": 150},
        {"label": _("Item Group"), "fieldname": "item_group",
         "fieldtype": "Link", "options": "Item Group", "width": 100},
        {"label": _("Warehouse"), "fieldname": "warehouse",
         "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _("Balance Qty"), "fieldname": "bal_qty",
         "fieldtype": "Float", "width": 100, "convertible": "qty"},
        {"label": _("Balance Value"), "fieldname": "bal_val",
         "fieldtype": "Currency", "width": 100},
        {"label": _("Qty 4"), "fieldname": "in_qty3",
         "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Value 4"), "fieldname": "in_val3",
         "fieldtype": "Float", "width": 80},
        {"label": _("Qty 3"), "fieldname": "in_qty2",
         "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Value 3"), "fieldname": "in_val2",
         "fieldtype": "Float", "width": 80},
        {"label": _("Qty 2"), "fieldname": "in_qty1",
         "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Value 2"), "fieldname": "in_val1",
         "fieldtype": "Float", "width": 80},
        {"label": _("Qty 1"), "fieldname": "in_qty0",
         "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Value 1"), "fieldname": "in_val0",
         "fieldtype": "Float", "width": 80},
        {"label": _("Older Qty"), "fieldname": "opening_qty",
         "fieldtype": "Float", "width": 100, "convertible": "qty"},
        {"label": _("Older Value"), "fieldname": "opening_val",
         "fieldtype": "Float", "width": 110}
    ]

    return columns


def get_conditions(filters):
    conditions = ""
    if not filters.get("from_date0"):
        frappe.throw(_("'From Date 1' is required"))

    if filters.get("to_date3"):
        conditions += " and sle.posting_date <= %s" % frappe.db.escape(
            filters.get("to_date3"))
    else:
        frappe.throw(_("'To Date 4' is required"))

    if filters.get("company"):
        conditions += " and sle.company = %s" % frappe.db.escape(
            filters.get("company"))

    if filters.get("warehouse"):
        warehouse_details = frappe.db.get_value("Warehouse",
                                                filters.get("warehouse"), ["lft", "rgt"], as_dict=1)
        if warehouse_details:
            conditions += " and exists (select name from `tabWarehouse` wh \
				where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)" % (warehouse_details.lft,
                                                                         warehouse_details.rgt)

    return conditions


def get_stock_ledger_entries(filters, items):
    item_conditions_sql = ''
    if items:
        item_conditions_sql = ' and sle.item_code in ({})'\
            .format(', '.join([frappe.db.escape(i, percent=False) for i in items]))

    conditions = get_conditions(filters)

    return frappe.db.sql("""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
			sle.item_code as name, sle.voucher_no, sle.voucher_type
		from
			`tabStock Ledger Entry` sle force index (posting_sort_index)
		where sle.docstatus < 2 %s %s
		order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty""" %  # nosec
                         (item_conditions_sql, conditions), as_dict=1)


def get_item_warehouse_map(filters, sle):
    iwb_map = {}

    from_date0 = getdate(filters.get("from_date0"))
    to_date0 = getdate(filters.get("to_date0"))

    from_date1 = getdate(filters.get("from_date1"))
    to_date1 = getdate(filters.get("to_date1"))

    from_date2 = getdate(filters.get("from_date2"))
    to_date2 = getdate(filters.get("to_date2"))

    from_date3 = getdate(filters.get("from_date3"))
    to_date3 = getdate(filters.get("to_date3"))

    float_precision = cint(frappe.db.get_default("float_precision")) or 3

    for d in sle:
        key = (d.company, d.item_code, d.warehouse)
        if key not in iwb_map:
            iwb_map[key] = frappe._dict({
                "opening_qty": 0.0, "opening_val": 0.0,
                "in_qty0": 0.0, "in_val0": 0.0,
                "in_qty1": 0.0, "in_val1": 0.0,
                "in_qty2": 0.0, "in_val2": 0.0,
                "in_qty3": 0.0, "in_val3": 0.0,
                "bal_qty": 0.0, "bal_val": 0.0
            })

        qty_dict = iwb_map[(d.company, d.item_code, d.warehouse)]

        if d.voucher_type == "Stock Reconciliation":
            qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
        else:
            qty_diff = flt(d.actual_qty)

        value_diff = flt(d.stock_value_difference)

        if d.posting_date < from_date0:
            qty_dict.opening_qty += qty_diff
            qty_dict.opening_val += value_diff
        elif d.posting_date >= from_date0 and d.posting_date <= to_date0:
            if(d.voucher_type == 'Sales Invoice' and d.actual_qty > 0):
                if(qty_dict.opening_qty > 0):
                    qty_dict.opening_qty += qty_diff
                    qty_dict.opening_val += value_diff
                else:
                    qty_dict.in_qty0 += qty_diff
                    qty_dict.in_val0 += value_diff
            elif flt(qty_diff, float_precision) >= 0:
                qty_dict.in_qty0 += qty_diff
                qty_dict.in_val0 += value_diff
        elif d.posting_date >= from_date1 and d.posting_date <= to_date1:
            if(d.voucher_type == 'Sales Invoice' and d.actual_qty > 0):
                if(qty_dict.opening_qty > 0):
                    qty_dict.opening_qty += qty_diff
                    qty_dict.opening_val += value_diff
                elif(qty_dict.in_qty0 > 0):
                    qty_dict.in_qty0 += qty_diff
                    qty_dict.in_val0 += value_diff
                else:
                    qty_dict.in_qty1 += qty_diff
                    qty_dict.in_val1 += value_diff
            elif flt(qty_diff, float_precision) >= 0:
                qty_dict.in_qty1 += qty_diff
                qty_dict.in_val1 += value_diff
        elif d.posting_date >= from_date2 and d.posting_date <= to_date2:
            if(d.voucher_type == 'Sales Invoice' and d.actual_qty > 0):
                if(qty_dict.opening_qty > 0):
                    qty_dict.opening_qty += qty_diff
                    qty_dict.opening_val += value_diff
                elif(qty_dict.in_qty0 > 0):
                    qty_dict.in_qty0 += qty_diff
                    qty_dict.in_val0 += value_diff
                elif(qty_dict.in_qty1 > 0):
                    qty_dict.in_qty1 += qty_diff
                    qty_dict.in_val1 += value_diff
                else:
                    qty_dict.in_qty2 += qty_diff
                    qty_dict.in_val2 += value_diff
            elif flt(qty_diff, float_precision) >= 0:
                qty_dict.in_qty2 += qty_diff
                qty_dict.in_val2 += value_diff
        elif d.posting_date >= from_date3 and d.posting_date <= to_date3:
            if(d.voucher_type == 'Sales Invoice' and d.actual_qty > 0):
                if(qty_dict.opening_qty > 0):
                    qty_dict.opening_qty += qty_diff
                    qty_dict.opening_val += value_diff
                elif(qty_dict.in_qty0 > 0):
                    qty_dict.in_qty0 += qty_diff
                    qty_dict.in_val0 += value_diff
                elif(qty_dict.in_qty1 > 0):
                    qty_dict.in_qty1 += qty_diff
                    qty_dict.in_val1 += value_diff
                elif(qty_dict.in_qty2 > 0):
                    qty_dict.in_qty2 += qty_diff
                    qty_dict.in_val2 += value_diff
                else:
                    qty_dict.in_qty3 += qty_diff
                    qty_dict.in_val3 += value_diff
            elif flt(qty_diff, float_precision) >= 0:
                qty_dict.in_qty3 += qty_diff
                qty_dict.in_val3 += value_diff

        qty_dict.bal_qty += qty_diff
        qty_dict.bal_val += value_diff

    iwb_map = filter_items_with_no_transactions(iwb_map, float_precision)
    iwb_map = dedicate_out_quintities(iwb_map)

    return iwb_map


def filter_items_with_no_transactions(iwb_map, float_precision):
    for (company, item, warehouse) in sorted(iwb_map):
        qty_dict = iwb_map[(company, item, warehouse)]

        no_transactions = True
        for key, val in iteritems(qty_dict):
            val = flt(val, float_precision)
            qty_dict[key] = val
            if key != "val_rate" and val:
                no_transactions = False

        if no_transactions:
            iwb_map.pop((company, item, warehouse))

    return iwb_map


def dedicate_out_quintities(iwb_map):
    for (company, item, warehouse) in sorted(iwb_map):
        qty_dict = iwb_map[(company, item, warehouse)]
        def_q = qty_dict.opening_qty + qty_dict.in_qty0 + qty_dict.in_qty1 + qty_dict.in_qty2 + qty_dict.in_qty3 - qty_dict.bal_qty
        def_v = qty_dict.opening_val + qty_dict.in_val0 + qty_dict.in_val1 + qty_dict.in_val2 + qty_dict.in_val3 - qty_dict.bal_val
        if(def_q > 0):
            if(qty_dict.opening_qty > 0):
                if(qty_dict.opening_qty >= def_q):
                    qty_dict.opening_qty = qty_dict.opening_qty - def_q
                    qty_dict.opening_val = qty_dict.opening_val - def_v
                    def_q = 0
                    def_v = 0
                else:
                    def_q = def_q - qty_dict.opening_qty
                    def_v = def_v - qty_dict.opening_val
                    qty_dict.opening_qty = 0
                    qty_dict.opening_val = 0
            if(qty_dict.in_qty0 > 0 and def_q > 0):
                if(qty_dict.in_qty0 >= def_q):
                    qty_dict.in_qty0 = qty_dict.in_qty0 - def_q
                    qty_dict.in_val0 = qty_dict.in_val0 - def_v
                    def_q = 0
                    def_v = 0
                else:
                    def_q = def_q - qty_dict.in_qty0
                    def_v = def_v - qty_dict.in_val0
                    qty_dict.in_qty0 = 0
                    qty_dict.in_val0 = 0
            if(qty_dict.in_qty1 > 0 and def_q > 0):
                if(qty_dict.in_qty1 >= def_q):
                    qty_dict.in_qty1 = qty_dict.in_qty1 - def_q
                    qty_dict.in_val1 = qty_dict.in_val1 - def_v
                    def_q = 0
                    def_v = 0
                else:
                    def_q = def_q - qty_dict.in_qty1
                    def_v = def_v - qty_dict.in_val1
                    qty_dict.in_qty1 = 0
                    qty_dict.in_val1 = 0
            if(qty_dict.in_qty2 > 0 and def_q > 0):
                if(qty_dict.in_qty2 >= def_q):
                    qty_dict.in_qty2 = qty_dict.in_qty2 - def_q
                    qty_dict.in_val2 = qty_dict.in_val2 - def_v
                    def_q = 0
                    def_v = 0
                else:
                    def_q = def_q - qty_dict.in_qty2
                    def_v = def_v - qty_dict.in_val2
                    qty_dict.in_qty2 = 0
                    qty_dict.in_val2 = 0
            if(qty_dict.in_qty3 > 0 and def_q > 0):
                qty_dict.in_qty3 = qty_dict.in_qty3 - def_q
                qty_dict.in_val3 = qty_dict.in_val3 - def_v

    return iwb_map


def get_items(filters):
    conditions = []
    if filters.get("item_code"):
        conditions.append("item.name=%(item_code)s")
    else:
        if filters.get("item_group"):
            conditions.append(get_item_group_condition(
                filters.get("item_group")))

    items = []
    if conditions:
        items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
                                   .format(" and ".join(conditions)), filters)
    return items


def get_item_details(items, sle, filters):
    item_details = {}
    if not items:
        items = list(set([d.item_code for d in sle]))

    if not items:
        return item_details

    cf_field = cf_join = ""

    res = frappe.db.sql("""
		select
			item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom %s
		from
			`tabItem` item
			%s
		where
			item.name in (%s)
	""" % (cf_field, cf_join, ','.join(['%s'] * len(items))), items, as_dict=1)

    for item in res:
        item_details.setdefault(item.name, item)

    return item_details


def validate_filters(filters):
    if not (filters.get("item_code") or filters.get("warehouse")):
        sle_count = flt(frappe.db.sql(
            """select count(name) from `tabStock Ledger Entry`""")[0][0])
        if sle_count > 500000:
            frappe.throw(
                _("Please set filter based on Item or Warehouse due to a large amount of entries."))
