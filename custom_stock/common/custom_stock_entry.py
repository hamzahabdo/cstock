from __future__ import unicode_literals
from warnings import filters
import frappe
from frappe import _, whitelist
from frappe.utils import data
from rstrnt.custom_restaurant.overrides.pos_invoice.custom_pos_invoice import get_stock_availability

def GetQty(item_code_list,warehouse,uom=None):
    data=[]
    for i in item_code_list:
        qty=get_stock_availability(i["item_code"],warehouse,uom)
        if qty>0:
            data.append({"item_code":i["item_code"],"UOM":i["uom"],"qty":qty,"conversion_factor":i["conversion_factor"]})
        # data.setdefault(i["item_scrap"], {}).update({"item_code":i["item_scrap"],"qty":y})
    return data

@frappe.whitelist(allow_guest=True)
def GetItemScrap(warehouse):
    formated_data=[]
    x=frappe.db.get_list("Scrap Item",fields=["item_scrap","item_uom"])
    for i in x:
        data=frappe.db.get_list("UOM Conversion Detail",filters={"parent":i["item_scrap"],'uom':i["item_uom"]},fields=['conversion_factor'])[0]
        formated_data.append({"item_code":i["item_scrap"],'uom':i['item_uom'],'conversion_factor':data["conversion_factor"]})
    return GetQty(formated_data,warehouse)