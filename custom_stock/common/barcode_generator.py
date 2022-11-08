import frappe
from frappe import _


@frappe.whitelist()
def get_last_barcode():
    pass
    # item = frappe.get_all(
    #     'Item',
    #     order_by="creation desc",
    #     limit_page_length=1
    # )
    # if item:
    #     barcode = frappe.get_doc('Item', item[0]).barcodes[0].barcode
    # else:
    #     barcode = "0000000000"

    # return str((int(barcode) + 1)).zfill(10)


def set_barcode(doc, method):
    barcode = get_last_barcode()

    if doc.barcodes:
        if len(doc.barcodes) > 0 and (not doc.barcodes[0].barcode
                                      or doc.barcodes[0].parent != doc.item_code):
            doc.barcodes[0].barcode = barcode
    else:
        doc.append('barcodes', {
            "barcode": barcode
        })
