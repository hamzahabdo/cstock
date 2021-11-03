# -*- coding: utf-8 -*-
# Copyright (c) 2020, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt
from erpnext.stock.utils import get_latest_stock_qty, get_stock_balance


class StockInventoryProcessing(Document):

    def validate(self):
        missing = []
        unsaved = []
        for document in self.stock_inventory_documents:
            inventory_doc = frappe.get_doc(
                "Stock Inventory", document.document_name)
            if inventory_doc.warehouse != self.warehouse:
                missing.append("<li><a href='#Form/"+inventory_doc.doctype+"/" +
                               document.document_name+"'>"+document.document_name)
            if inventory_doc.docstatus != 0:
                unsaved.append("<li><a href='#Form/"+inventory_doc.doctype+"/" +
                               document.document_name+"'>"+document.document_name)

        if missing:
            frappe.throw(
                _("Warehouse is not consistant in the following:")
                + "<ul>" + "</a></li>".join(missing))
        # elif unsaved:
        #     frappe.throw(
        #         _("The following documents are either submitted or cancelled:")
        #         + "<ul>" + "</a></li>".join(unsaved))

    def before_submit(self):
        missing = []
        for document in self.stock_inventory_documents:
            status = frappe.get_doc(
                "Stock Inventory", document.document_name)
            if status.docstatus != 1:
                missing.append("<li><a href='#Form/"+status.doctype+"/" +
                               document.document_name+"'>"+document.document_name)
        if missing:
            frappe.throw(
                _("You cannot submit this document until you submit the following:")
                + "<ul>" + "</a></li>".join(missing))


def get_inventoried_items(docs):

    def get_items_from_inventory_documents(is_listed=True, data=None):
        if is_listed:
            bin_columns = 'bin.actual_qty as a_qty, bin.valuation_rate as rate'
            bin_condition = 'child.item_code = bin.item_code and par.warehouse = bin.warehouse and'
            bin_tables = '`tabStock Inventory Item` child, `tabStock Inventory` par, `tabBin` bin'
        else:
            bin_columns = '0 as a_qty,  0 as rate'
            bin_condition = ''
            if data:
                bin_condition = "child.item_code not in ('{}') and".format(data)
            bin_tables = '`tabStock Inventory Item` child, `tabStock Inventory` par'

        columns = """
            child.item_code, child.item_name, child.item_group, 
            sum(abs(child.qty)) as qty, {}
        """.format(bin_columns)

        conditoin = """
                {0} child.parent = par.name and par.name in {1}
        """.format(bin_condition, docs) 

        inventoried_items = frappe.db.sql("""
            select {0}
            from
                {1}
            where
                {2}
            group by item_code
        """.format(columns, bin_tables, conditoin), as_dict=1)

        return inventoried_items

    inventoried_items = get_items_from_inventory_documents()

    # bin_columns = 'bin.actual_qty as a_qty, bin.valuation_rate as rate'
    # bin_condition = 'child.item_code = bin.item_code and par.warehouse = bin.warehouse'
    # bin_tables = '`tabStock Inventory Item` child, `tabStock Inventory` par, `tabBin` bin'
    # columns = """
    #     child.item_code, child.item_name, child.item_group,
    #     sum(abs(child.qty)) as qty, {}
    #     """.format(bin_columns)
    # columns1 = """
    #     child.item_code, child.item_name, child.item_group,
    #     sum(abs(child.qty))as qty,
    #     0 as a_qty,  0 as rate
    #     """
    # conditoin = """child.item_code = bin.item_code and par.warehouse = bin.warehouse
    #             and child.parent = par.name and par.name in {0}""".format(
    #     docs)

    # inventoried_items = frappe.db.sql("""
    #     select {0}
    # 	from
    # 		`tabStock Inventory Item` child, `tabStock Inventory` par, `tabBin` bin
    # 	where
    # 		{1}
    # 	group by item_code
    # """.format(columns, conditoin), as_dict=1)
    unlisted_items = []
    data = "','".join(list(map(lambda item: item.item_code, inventoried_items)))
    if data:
        unlisted_items = get_items_from_inventory_documents(False, data)
    else:
        unlisted_items = get_items_from_inventory_documents(False)

    # conditoin1 = """child.item_code not in ({1})
    #             and child.parent = par.name and par.name in {0}""".format(
    #     docs, data)

    # unlisted_items = frappe.db.sql("""
    #     select {0}
    # 	from
    # 		`tabStock Inventory Item` child, `tabStock Inventory` par
    # 	where
    # 		{1}
    # 	group by item_code
    # """.format(columns1, conditoin1), as_dict=1)
    # print(list(unlisted_items))

    inventoried_items += unlisted_items

    return inventoried_items


# def get_uninventoried_items(args, item_group, price_list, all_items):

#     columns = "distinct price.item_code, price.item_name, item.item_group, 0 as qty "
#     tables = "`tabItem` item, `tabItem Price` price"
#     # tables = "`tabItem` item"
#     source_table = "item.item_group = '{0}' and price.price_list = '{1}'".format(
#         item_group, price_list)

#     if cint(all_items):
#         source_table = "price.price_list = '{0}'".format(price_list)

#     conditoin = """ {0} and price.item_code = item.item_code and price.item_code not in (select child.item_code
#     from `tabStock Inventory Item` child, `tabStock Inventory` par
#     where child.parent = par.name and par.name in {1} )""".format(source_table, args)

#     uninventoried_items = frappe.db.sql("""
#         select {0}
# 		from
#             {1}
# 		where
# 			{2}
# 		group by item_code
#     """.format(columns, tables, conditoin), as_dict=1)
#     return uninventoried_items


def get_uninventoried_items(docs, warehouse, groups):
    item_group = ''
    data = []

    if groups:
        item_group = "and item.item_group in {}".format(groups)

        data = frappe.db.sql("""
                select
                    sle.item_code,
                    sle.valuation_rate as rate,
                    sle.actual_qty as a_qty,
                    0 as qty,
                    item.item_group, item.item_name
                from
                    `tabBin` sle, `tabItem` item
                where
                    sle.docstatus < 2 and warehouse = '{0}'
                    and sle.actual_qty != 0
                    and sle.item_code = item.item_code {1}
                    and sle.item_code not in (
                        select child.item_code
                        from `tabStock Inventory Item` child, `tabStock Inventory` par
                        where child.parent = par.name and par.name in {2} )
                group by sle.item_code
                """.format(warehouse, item_group, docs), as_dict=1)
    return data


@ frappe.whitelist()
def get_inventory_items(docs, warehouse, item_groups=None, all_items=False):

    data = get_inventoried_items(docs)
    _data = None
    if cint(all_items):
        _data = get_uninventoried_items(docs, warehouse, item_groups)
        data = data + _data

    return data

# @frappe.whitelist()
# def get_inventory_items(args, warehouse, price_list=None, is_item_group=False, item_group=None, all_items=False):

#     data = get_inventoried_items(args)
#     # region
#     # columns = "child.item_code, child.item_name, child.item_group, sum(abs(child.qty)) as qty"
#     # conditoin = "child.parent = par.name and par.name in {0}".format(args)
#     # tables = "`tabStock Inventory Item` child, `tabStock Inventory` par"

#     # data = frappe.db.sql("""
#     #     select {0}
#     #     from
#     #         {1}
#     #     where
#     #         {2}
#     #     group by item_code
#     # """.format(columns, tables, conditoin), as_dict=1)
#     # endregion

#     if cint(all_items) or cint(is_item_group):
#         _data = get_uninventoried_items(
#             args, item_group, price_list, all_items)
#         # else:
#         #     _data = get_uninventoried_items(
#         #         args, item_group, price_list, all_items)
#         data = data + _data
#         # region
#         # columns = "item.item_code, item.item_name, item.item_group, 0 as qty "
#         # conditoin = """item.item_group = '{0}' and item.item_code not in (select child.item_code
#         # from `tabStock Inventory Item` child, `tabStock Inventory` par
#         # where child.parent = par.name and par.name in {1} )""".format(item_group, args)
#         # tables = "`tabItem` item"

#         # _data = (frappe.db.sql("""
#         #     select {0}
#         #     from
#         #         {1}
#         #     where
#         #         {2}
#         #     group by item_code
#         # """.format(columns, tables, conditoin), as_dict=1))
#         # endregion
#         # data = get_inventoried_items(args)

#     items = {}
#     for d in data:
#         stock_balance = get_stock_balance(
#             d.get("item_code"), warehouse, with_valuation_rate=True)

#         if stock_balance[0] < 0:
#             frappe.throw(
#                 _("Please, reconciliate negative quantities in warehouse: {}!".format(warehouse)))
#         if (stock_balance[0] - flt(d.qty)) != 0:
#             items.setdefault(d.item_code, frappe._dict({
#                 "item_code": d.item_code,
#                 "item_name": d.item_name,
#                 "item_group": d.item_group,
#                 "qty": d.qty,
#                 "a_qty": stock_balance[0] or 0,
#                 "rate": stock_balance[1]
#                 # get_latest_stock_qty(d.get("item_code"), warehouse) or 0
#             }))

#     return items
