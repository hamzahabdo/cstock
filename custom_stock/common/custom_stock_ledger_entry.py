import json
import frappe
from frappe import _
from frappe.utils.data import flt, format_time
from erpnext.stock.stock_ledger import NegativeStockError, get_previous_sle


def check_actual_qty(doc, method):
    allow_negative_stock = frappe.get_all("Warehouse", filters={
                                          "name": doc.warehouse}, fields=["_allow_negative_stock"])[0]

    if(doc.actual_qty > 0 or allow_negative_stock["_allow_negative_stock"]):
        return

    previous_sle = get_previous_sle({
        "item_code": doc.item_code,
        "warehouse": doc.warehouse,
        "posting_date": doc.posting_date,
        "posting_time": doc.posting_time
    })

    # get actual stock at source warehouse
    qty_after_transaction = previous_sle.get("qty_after_transaction") or 0

    # validate qty during submit
    if abs(flt((doc.actual_qty))) > flt(qty_after_transaction):

        frappe.throw(_("Row {0}: Quantity not available for {3} in warehouse {1} at posting time of the entry ({2})").format(doc.idx, frappe.bold(doc.warehouse), format_time(doc.posting_time), frappe.bold(doc.item_code))
                     + '<br><br>' + _("Available quantity is {0}, you need {1}").format(frappe.bold(doc.actual_qty), frappe.bold(qty_after_transaction)), NegativeStockError, title=_('Insufficient Stock'))
