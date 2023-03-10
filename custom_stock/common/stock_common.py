# Copyright (c) 2022,burjalmaha Team and Contributors

from __future__ import unicode_literals
from traceback import print_tb
import frappe
from frappe import _
from erpnext.stock.utils import get_latest_stock_qty
from erpnext.stock.utils import get_stock_balance
from frappe.utils import flt, cstr, cint


def get_current_account(warehouse):
    branch = frappe.get_doc('Warehouse', warehouse).branch
    return frappe.get_doc('Branch', branch).currant_account


def make_gl_entry(doc, account, current_account, reverse):
    if account.debit or account.credit:
        gl_entry = doc.get_gl_dict({
            "account": current_account,
            "posting_date": account.posting_date,
            "debit": (account.debit, account.credit)[reverse],
            "credit": (account.credit, account.debit)[reverse],
            "account_currency": account.account_currency,
            "debit_in_account_currency": (account.debit_in_account_currency, account.credit_in_account_currency)[reverse],
            "credit_in_account_currency": (account.credit_in_account_currency, account.debit_in_account_currency)[reverse],
            "voucher_no": account.voucher_no,
            "remarks": account.remarks,
            "cost_center": account.cost_center,
            "project": account.project
        }, item=account)
        gl_entry.branch = doc.branch
        return gl_entry


def get_intermediate_account(doc):
    return frappe.get_doc(
        "Warehouse", frappe.get_doc(
            "Warehouse", doc.from_warehouse).default_in_transit_warehouse).account


def make_current_account_entries(doc, method):

    if doc.get("purpose") == "Material Transfer":
        gl_entries = []
        current_account = None
        # if(doc.get("purpose") == "Send to Warehouse"):
        if(not doc.get("outgoing_stock_entry")):
            current_account = get_current_account(doc.target_warehouse)
        # elif(doc.get("purpose") == "Receive at Warehouse"):
        elif(doc.get("outgoing_stock_entry")):
            current_account = get_current_account(doc.source_warehouse)
        intermediate_account = get_intermediate_account(doc)
        if not (current_account and intermediate_account):
            frappe.throw(_('Could not make current account entries'))
        entries = frappe.get_list(
            "GL Entry", filters={"voucher_no": doc.name, "account": intermediate_account})

        intermediate_account_entry = frappe.get_doc("GL Entry", entries[0])
        gl_entries.append(make_gl_entry(
            doc, intermediate_account_entry, current_account, False))
        gl_entries.append(make_gl_entry(
            doc, intermediate_account_entry, intermediate_account, True))

        from erpnext.accounts.general_ledger import make_gl_entries
        make_gl_entries(gl_entries)


def get_future_stock_vouchers(posting_date, posting_time, for_warehouses=None, for_items=None):
    future_stock_vouchers = []

    values = []
    condition = ""
    if for_items:
        condition += " and item_code in ({})".format(
            ", ".join(["%s"] * len(for_items)))
        values += for_items

    if for_warehouses:
        condition += " and warehouse in ({})".format(
            ", ".join(["%s"] * len(for_warehouses)))
        values += for_warehouses

    for d in frappe.db.sql("""select distinct sle.voucher_type, sle.voucher_no
		from `tabStock Ledger Entry` sle
		where timestamp(sle.posting_date, sle.posting_time) > timestamp(%s, %s) {condition}
		order by timestamp(sle.posting_date, sle.posting_time) asc, creation asc for update""".format(condition=condition),
                           tuple([posting_date, posting_time] + values), as_dict=True):
        future_stock_vouchers.append([d.voucher_type, d.voucher_no])

    return future_stock_vouchers


def check_future_transactions(doc, method):
    # this function ensures transactions with future entries can not be canceled,
    # do not disable it until solving current account issue
    if(frappe.get_single("Common Stock Setting").disable_future_stock_transaction_check):
        return
    items, warehouses = doc.get_items_and_warehouses()
    future_stock_vouchers = get_future_stock_vouchers(
        doc.posting_date, doc.posting_time, warehouses, items)
    if future_stock_vouchers:
        msg = ""
        for voucher_type, voucher_no in future_stock_vouchers:
            msg = msg + voucher_type + ": " + voucher_no + ", "
        frappe.throw(_("There is futrue transactions: ") + msg)


def assign_override_methods(doc, method):
    from erpnext.controllers.stock_controller import StockController
    StockController.get_gl_entries = get_gl_entries


def get_gl_entries(self, warehouse_account=None, default_expense_account=None,
                   default_cost_center=None):

    if not warehouse_account:
        print(self.company)
        from erpnext.stock import get_warehouse_account_map
        warehouse_account = get_warehouse_account_map(self.company)

    sle_map = self.get_stock_ledger_details()
    voucher_details = self.get_voucher_details(
        default_expense_account, default_cost_center, sle_map)

    gl_list = []
    warehouse_with_no_account = []

    precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
    for item_row in voucher_details:
        sle_list = sle_map.get(item_row.name)
        if sle_list:
            for sle in sle_list:
                if warehouse_account.get(sle.warehouse):
                    # from warehouse account

                    self.check_expense_account(item_row)

                    if not sle.stock_value_difference and self.doctype != "Stock Reconciliation" \
                            and not item_row.get("allow_zero_valuation_rate"):

                        sle = self.update_stock_ledger_entries(sle)
                    from frappe.utils import flt
                    gl_list.append(self.get_gl_dict({
                        "account": warehouse_account[sle.warehouse]["account"],
                        "against": item_row.expense_account,
                        "cost_center": item_row.cost_center,
                        "remarks": self.get("remarks") or "Accounting Entry for Stock",
                        "debit": flt(sle.stock_value_difference, precision),
                        "is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
                    }, warehouse_account[sle.warehouse]["account_currency"], item=item_row))

                    # to target warehouse / expense account
                    gl_list.append(self.get_gl_dict({
                        "account": item_row.expense_account,
                        "against": warehouse_account[sle.warehouse]["account"],
                        "cost_center": item_row.cost_center,
                        "remarks": self.get("remarks") or "Accounting Entry for Stock",
                        "credit": flt(sle.stock_value_difference, precision),
                        "project": item_row.get("project") or self.get("project"),
                        "is_opening": item_row.get("is_opening") or self.get("is_opening") or "No"
                    }, item=item_row))

                elif sle.warehouse not in warehouse_with_no_account:
                    warehouse_with_no_account.append(sle.warehouse)
    if warehouse_with_no_account:
        for wh in warehouse_with_no_account:
            if frappe.db.get_value("Warehouse", wh, "company"):
                frappe.throw(_("Warehouse {0} is not linked to any account, please mention the account in  the warehouse record or set default inventory account in company {1}.").format(
                    wh, self.company))

    from erpnext.accounts.general_ledger import process_gl_map

    processed_gl_map = process_gl_map(gl_list)
    if self.get("purpose") == "Material Transfer" and (self.get("add_to_transit") or self.get("outgoing_stock_entry")):

        # intermediate_warehouse = frappe.get_doc(
        #     "NCITY Settings").intermediate_warehouse
        intermediate_warehouse = frappe.get_doc(
            "Warehouse", self.source_warehouse).default_in_transit_warehouse

        intermediate_account = frappe.get_doc(
            "Warehouse", intermediate_warehouse).account
        target_current_account = get_current_account(self.target_warehouse)
        source_current_account = get_current_account(self.source_warehouse)

        if not (source_current_account == target_current_account):
            flag = 0
            for entry in processed_gl_map:
                if(entry.account == intermediate_account):
                    flag = 1
                    current_account = None

                    if(self.get("purpose") == "Material Transfer" and not self.outgoing_stock_entry):
                        current_account = target_current_account

                    elif(self.get("purpose") == "Material Transfer" and self.outgoing_stock_entry):
                        current_account = source_current_account

                    intermediate = entry.copy()
                    intermediate.account = current_account

                    processed_gl_map.append(intermediate)

                    if(entry.credit > 0):
                        entry.debit = entry.credit
                    else:
                        entry.credit = entry.debit
                    break

            if not flag:
                frappe.throw("No Intermediate Warehouse Account")

    return processed_gl_map


def validate_stock_keeper(doc, method):
    if frappe.session.user == "Administrator":
        return

    valid = False
    message = ""
    if((doc.purpose == "Material Transfer" and not doc.outgoing_stock_entry) or doc.purpose == "Material Issue" or doc.purpose == "Manufacture" or doc.purpose == "Material Transfer for Manufacture"):
        message = "Sorry, You can not send from this warehouse"
        warehouse = None
        if doc.from_warehouse:
            warehouse = doc.from_warehouse 
        else :
            warehouse = doc.source_warehouse
        
        keepers = frappe.get_doc(
            "Warehouse", warehouse).stock_keeper_users
        
        print(keepers)
        for keeper in keepers:
            if(frappe.session.user == keeper.user and keeper.send_to_warehouse):
                valid = True
                break

    elif((doc.purpose == "Material Transfer" and doc.outgoing_stock_entry) or doc.purpose == "Material Receipt"):
        message = "Sorry, You can not receive at this warehouse"
        keepers = frappe.get_doc(
            "Warehouse", doc.to_warehouse).stock_keeper_users
        for keeper in keepers:
            if(frappe.session.user == keeper.user and keeper.receive_at_warehouse):
                valid = True
                break

    if(not valid):
        frappe.throw(_(message))


@frappe.whitelist()
def get_ongoing_stock_entry(entry):
    return frappe.get_doc('Stock Entry', entry)


@frappe.whitelist()
def get_warehouse_branch(warehouse):
    return frappe.get_doc('Warehouse', warehouse)


def set_branch(doc, method):
    if (doc.purpose == "Material Transfer" and doc.outgoing_stock_entry) or doc.purpose == "Material Receipt":
        _branch = frappe.get_doc('Warehouse', doc.to_warehouse)
    else:
        warehouse = None
        if doc.from_warehouse:
            warehouse = doc.from_warehouse 
        else :
            warehouse = doc.source_warehouse
            
        _branch = frappe.get_doc('Warehouse', warehouse)

    branch = _branch.branch
    doc.set("branch", branch)
    for item in doc.items:
        if doc.purpose == "Material Issue" or doc.purpose == "Material Receipt":
            item.set("expense_account", doc.expense_account)
        item.set("branch", branch)


@frappe.whitelist()
def get_qty_at_warehouse(item_code, warehouse):
    qty = get_latest_stock_qty(item_code, warehouse)

    if qty == None:
        qty = 0.0
    return qty


@frappe.whitelist()
def get_negative_items(warehouse):
    lft, rgt = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"])
    items = frappe.db.sql("""
		select i.name, i.item_name, bin.warehouse, bin.actual_qty, bin.valuation_rate
		from tabBin bin, tabItem i
		where i.name=bin.item_code and i.disabled=0 and i.is_stock_item = 1
		and i.has_variants = 0 and i.has_serial_no = 0 and i.has_batch_no = 0 and actual_qty < 0
		and exists(select name from `tabWarehouse` where lft >= %s and rgt <= %s and name=bin.warehouse)
	""", (lft, rgt))

    res = []
    for d in set(items):
        res.append({
            "item_code": d[0],
            "warehouse": d[2],
            "qty": d[3],
            "item_name": d[1],
            "valuation_rate": d[4],
            "current_qty": d[3],
            "current_valuation_rate": d[4]
        })

    return res


def ibmx(doctype, txt, searchfield, start, page_len, filters):
    conditions = []

    item_code_list1 = frappe.db.sql(
        "select distinct(ED.item_code) from `tabStock Entry` E,`tabStock Entry Detail` ED  where E.name=ED.parent  and  E.to_warehouse='" + filters.get("stock_entry_type") + "'")

    for item_code in item_code_list1:
        qty = get_stock_balance(
            item_code[0], filters.get("stock_entry_type"))
        if qty > 0:
            conditions.append(item_code[0])

    item_code_list2 = frappe.db.sql(
        "select distinct(I.item_code) from `tabStock Reconciliation Item` I,`tabStock Reconciliation` R  where R.name=I.parent  and  R.warehouse='" + filters.get("stock_entry_type") + "' and purpose='Opening Stock'")

    for item_code2 in item_code_list2:
        qty = get_stock_balance(
            item_code2[0], filters.get("stock_entry_type"))
        if qty > 0:
            conditions.append(item_code2)

    conditions = tuple(conditions)

    return conditions


@frappe.whitelist()
def get_available_items(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """select item_code from tabBin
                where warehouse='{warehouse}'
                and actual_qty > 0
	            and item_code like %(txt)s
	            limit %(start)s, %(page_len)s""".format(**{'warehouse': filters.get("warehouse")}),
        {
            'txt': "%%%s%%" % txt,
            '_txt': txt.replace("%", ""),
            'start': start,
            'page_len': page_len
        })


@frappe.whitelist()
def get_inventory_items(warehouse, inventory, qty):
    if qty == 1:
        qty_condition = "and i.difference_qty > 0 "
    elif qty == -1:
        qty_condition = "and i.difference_qty < 0 "
    else:
        qty_condition = ""

    items = frappe.db.sql("""
		select i.item_code, i.item_name, p.warehouse, i.inventory_qty, i.rate, i.difference_qty
		from
            `tabStock Inventory Processing Item` i, `tabStock Inventory Processing` p
		where
            i.parent=p.name and p.docstatus=1 and p.warehouse='{0}' and p.name='{1}' {2}
	""".format(warehouse, inventory, qty_condition))

    res = []
    for d in set(items):

        if frappe.db.get_value("Item", d[0], "disabled") == 0:
            res.append({
                "item_code": d[0],
                "warehouse": d[2],
                "qty": d[3],
                "item_name": d[1],
                "valuation_rate": d[4],
                "current_qty": d[3],
                "current_valuation_rate": d[4]
            })

    return res


def validate_for_items(doc, method):
    allow_multi_item = frappe.get_doc(
        "Custom Stock Setting").allow_multiple_items
    if allow_multi_item == 0:
        check_list = []
        for d in doc.get("items"):
            if d.item_code in check_list:
                frappe.throw(
                    _("Row# {0}: Item {1} entered more than once").format(d.idx, d.item_code))
            else:
                check_list.append(d.item_code)


@frappe.whitelist()
def get_warehouse_acronym(wname):
    warehouse = frappe.get_doc('Warehouse', wname)
    return warehouse.short_name


@frappe.whitelist()
def get_in_transit_warehous(wname):
    warehouse = frappe.get_doc('Warehouse', wname)
    return warehouse.default_in_transit_warehouse


@frappe.whitelist()
def test_get_warehouse_acronym(wname):
    warehouse = frappe.get_doc('Warehouse', wname)
    message_dic = {"short_name": warehouse.short_name,
                   "transit_warehouse": warehouse.default_in_transit_warehouse}
    print(frappe.as_json(message_dic))
    message = frappe.as_json(message_dic)
    return message_dic


@frappe.whitelist()
def override_scan_barcode():
    from erpnext.selling.page.point_of_sale import point_of_sale as pos
    pos.search_serial_or_batch_or_barcode_number = search_serial_or_batch_or_barcode_number


@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value):
    # search barcode no
    barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, [
                                       'barcode', 'parent as item_code'], as_dict=True)

    if not barcode_data:
        barcode_data = frappe.db.get_value('Item Barcode', {'parent': search_value}, [
                                           'barcode', 'parent as item_code'], as_dict=True)

    if barcode_data:
        return barcode_data

    # search serial no
    serial_no_data = frappe.db.get_value('Serial No', search_value, [
                                         'name as serial_no', 'item_code'], as_dict=True)
    if serial_no_data:
        return serial_no_data

    # search batch no
    batch_no_data = frappe.db.get_value(
        'Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
    if batch_no_data:
        return batch_no_data

    return {}


def validate_add_to_transit(doc, method):
    if(doc.purpose == 'Material Transfer' and not doc.outgoing_stock_entry and not doc.add_to_transit):
        if(doc.from_warehouse and doc.to_warehouse):
            from_current_warehouse = get_current_account(doc.from_warehouse)
            to_current_warehouse = get_current_account(doc.to_warehouse)
            if(from_current_warehouse != to_current_warehouse):
                frappe.throw(
                    _('<b>Check Add To Transit</b>  The Trannsaction Is Between Different Branches'))


def CheckConversionFactor(doc, method):
    for i in doc.items:
        if i.uom != i.stock_uom and float(i.conversion_factor) == 1:
            frappe.throw(
                "Check the Conversion Factor for Item Code:{0}".format(i.item_code))
        elif i.uom == i.stock_uom and int(i.conversion_factor) != 1:
            frappe.throw(
                "The Conversion Factor for Item Code:{0} should be 1".format(i.item_code))
