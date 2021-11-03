import frappe


@frappe.whitelist()
def get_single_doc(doctype):
    return frappe.get_doc(doctype, doctype)


@frappe.whitelist()
def get_doc(doctype, docname):
    return frappe.get_doc(doctype, docname)
