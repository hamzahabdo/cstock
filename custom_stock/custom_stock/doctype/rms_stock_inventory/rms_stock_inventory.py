import re
from frappe.model.document import Document
import frappe
from frappe import _, parse_json
from erpnext.stock.stock_ledger import get_previous_sle


class RMSStockInventory(Document):
    pass


def GetBranch(warehouse):
    Branch = frappe.get_all("Warehouse", filters={
                            "name": warehouse}, fields=["branch"])
    return Branch[0]["branch"]


@frappe.whitelist()
def get_item_uom(item_code):
    return frappe.get_all("UOM Conversion Detail", filters={
        "parent": item_code}, fields=["uom", "conversion_factor"])


@frappe.whitelist()
def get_conversion(item_code, uom):
    return frappe.get_all("UOM Conversion Detail", filters={"parent": item_code, "uom": uom}, fields=["conversion_factor"])


def filter_uom(items):
    tmp_obj = {}
    for i in items:
        for y in i:
            if(y["item_code"] in tmp_obj.keys()):
                tmp_obj[y["item_code"]
                        ]["stock_qty"] = tmp_obj[y["item_code"]]["stock_qty"]+y["stock_qty"]
            else:
                x = {y["item_code"]: y}
                tmp_obj.update(x)
    return tmp_obj


def dispose_of_goods(items, account, warehouse, doc_name):
    if items:
        data = frappe.new_doc("Stock Entry")
        data.stock_entry_type = "صرف مخزني"
        data.purpose = "Material Issue"
        data.expense_account = account
        data.from_warehouse = warehouse
        data.source_warehouse = warehouse
        data.sw = frappe.get_doc('Warehouse', warehouse).short_name
        data.tw = frappe.get_doc('Warehouse', warehouse).short_name
        for i in items:
            if(i["stock_qty"] > 0):
                data.append('items', {
                            "item_code": i["item_code"],
                            "qty": i["stock_qty"],
                            "transfer_qty": i["stock_qty"],
                            "uom": i["stock_uom"],
                            "s_warehouse": warehouse,
                            "branch": GetBranch(warehouse)})
        if(hasattr(data, "items")):
            data.insert()
            ref = data.name
            # data.submit()
            frappe.db.set_value(
                'RMS Stock Inventory', doc_name.name, 'stock_item_release_reference', ref)


def supply_of_goods(items, account, warehouse, doc_name):
    if items:
        data = frappe.new_doc("Stock Entry")
        data.stock_entry_type = "توريد مخزني"
        data.purpose = "Material Receipt"
        data.expense_account = account
        data.target_warehouse = warehouse
        data.to_warehouse = warehouse
        data.sw = frappe.get_doc('Warehouse', warehouse).short_name
        data.tw = frappe.get_doc('Warehouse', warehouse).short_name
        for i in items:
            if(i["stock_qty"] > 0):
                data.append('items', {
                            "item_code": i["item_code"],
                            "qty": i["stock_qty"],
                            "transfer_qty": i["stock_qty"],
                            "uom": i["stock_uom"],
                            "t_warehouse": warehouse,
                            "branch": GetBranch(warehouse)})
        if(hasattr(data, "items")):
            data.insert()
            ref = data.name
            # data.submit()
            frappe.db.set_value(
                'RMS Stock Inventory', doc_name.name, 'stock_item_supply_reference', ref)


@ frappe.whitelist()
def get_stock_ledger_entries(doc):
    positive = []
    negative = []
    da = parse_json(doc)
    rms_s_i = frappe.get_doc('RMS Stock Inventory', da["name"])

    tmp_list = []
    tmp_list.append(da["items"])
    items = filter_uom(tmp_list)
    for i in items:
        previous_sle = get_previous_sle({
            "item_code": items[i]["item_code"],
            "warehouse": da["warehouse"],
            "posting_date": da["posting_date"],
            "posting_time": da["posting_time"]
        })
        # get actual stock at source warehouse
        qty_after_transaction = previous_sle.get("qty_after_transaction") or 0
        amount = qty_after_transaction-items[i]["stock_qty"]
        if amount < 0:
            items[i]["stock_qty"] = abs(amount)
            positive.append(items[i])
        else:
            items[i]["stock_qty"] = amount
            negative.append(items[i])
    dispose_of_goods(
        negative, da["settlement_account"], da["warehouse"], rms_s_i)
    supply_of_goods(positive, da["settlement_account"],
                    da["warehouse"], rms_s_i)


@frappe.whitelist()
def get_all_items(warehouse, posting_date):
    sql = """SELECT DISTINCT(sle.item_code),ti.stock_uom,ti.item_name
            FROM `tabStock Ledger Entry` sle
                        join `tabItem` ti ON ti.item_code = sle.item_code
            WHERE sle.posting_date <= '{0}'
            AND sle.warehouse = '{1}'
            AND ti.is_insurance_item = 0""".format(posting_date, warehouse)
    return frappe.db.sql(sql, as_dict=True)
