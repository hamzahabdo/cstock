# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
#from frappe.utils import flt
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):
	columns = [	_(filters.get("Group_By")) + "::340",  _("Quantity") + "::200",  _("Price") + "::200" ]

	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("Item"): 		conditions += " and SED.item_code = %(Item)s"
	if filters.get("Item_Group"): 	conditions += " and SED.item_group = %(Item_Group)s"
	if filters.get("Warehouse"): 	conditions += " and SED.t_warehouse = %(Warehouse)s"
	if filters.get("Supplier"): 	conditions += " and I.N_Supplier = %(Supplier)s"							 	
	conditions += " and SE.posting_date between  %(from_date)s"
	conditions += " and  %(to_date)s"

	if filters.get("Group_By") == 'Suplier': 	conditions += " Group by I.N_Supplier"
	if filters.get("Group_By") == 'Item Group': conditions += " Group by SED.item_group"
	if filters.get("Group_By") == 'Warehouse':  conditions += " Group by SED.t_warehouse"
	if filters.get("Group_By") == 'Item': 		conditions += " Group by SED.item_code"

	return conditions, filters

def get_data(filters):
	conditions, filters = get_conditions(filters)
	if	filters.get("Group_By") == "Suplier":
		Select_Group 	 = frappe.db.sql("""select I.N_SUPPLIER    Collection, Sum(QTY) count, Sum(SED.basic_amount) valuation_rate from `tabStock Entry` SE, `tabStock Entry Detail` SED ,`tabItem` I where SE.name=SED.parent and SED.item_code=I.item_code and SE.stock_entry_type='Receive at Warehouse' %s """ % conditions, filters, as_dict=1)
	elif filters.get("Group_By") == "Item Group":
		Select_Group 	 = frappe.db.sql("""select SED.item_group  Collection, Sum(QTY) count, Sum(SED.basic_amount) valuation_rate from `tabStock Entry` SE, `tabStock Entry Detail` SED ,`tabItem` I where SE.name=SED.parent and SED.item_code=I.item_code and SE.stock_entry_type='Receive at Warehouse' %s """ % conditions, filters, as_dict=1)
	elif filters.get("Group_By") == "Warehouse":
		Select_Group 	 = frappe.db.sql("""select SED.t_warehouse Collection, Sum(QTY) count, Sum(SED.basic_amount) valuation_rate from `tabStock Entry` SE, `tabStock Entry Detail` SED ,`tabItem` I where SE.name=SED.parent and SED.item_code=I.item_code and SE.stock_entry_type='Receive at Warehouse' %s """ % conditions, filters, as_dict=1)
	elif filters.get("Group_By") == "Item":
		Select_Group 	 = frappe.db.sql("""select SED.item_code   Collection, Sum(QTY) count, Sum(SED.basic_amount) valuation_rate from `tabStock Entry` SE, `tabStock Entry Detail` SED ,`tabItem` I where SE.name=SED.parent and SED.item_code=I.item_code and SE.stock_entry_type='Receive at Warehouse' %s """ % conditions, filters, as_dict=1)

	data = []
	for items in Select_Group:
		row = [items.Collection ,items.count,items.valuation_rate]
				
		data.append(row)
	return data