from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now, date_diff
from erpnext.stock.utils import add_additional_uom_columns
import json


from six import iteritems


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    items = get_items(filters)
    
    group_by_data = []
    if(filters.s_warehouse):
        _filters = frappe.parse_json({
            "company": filters.company,
            "from_date": filters.from_date,
            "to_date": filters.to_date,
            "item_group": filters.item_group,
            "group_by": "Item",
            "warehouse": filters.s_warehouse
        })
        s_group_by_data = get_data(_filters, items)
        s_items = []
        if(filters.com == _("Greater Than")):
            com = ">"
        elif(filters.com == _("Equal")):
            com = "=="
        for i in s_group_by_data:
            con = "{} {} {}".format(i["bal_qty"], com, filters.qty)
            if(eval(con)):
                s_items.append(i["item_code"])
        group_by_data = get_data(filters, s_items)
    else:
        group_by_data = get_data(filters, items)

    return columns, group_by_data

def get_data(filters, items):
    sle = get_stock_ledger_entries(filters, items)

    # if no stock ledger entry found return
    if not sle:
        return []

    iwb_map = get_item_warehouse_map(filters, sle)
    item_map = get_item_details(items, sle, filters)

    data = []

    for (company, item, warehouse) in sorted(iwb_map):
        if item_map.get(item):
            qty_dict = iwb_map[(company, item, warehouse)]

            report_data = {
                'warehouse': warehouse
            }
            report_data.update(item_map[item])
            report_data.update(qty_dict)
            data.append(report_data)      
    group_by = get_group_by(filters.get("group_by"))  
    group_by_data = []
    for i in data:
        row = get_or_make_row(group_by_data, group_by, i[group_by])
        if filters.get('group_by') == "Item":
            item_name = get_item_name_from_item_code(i['item_code'])
            row['item_name']  = item_name
            row['item_group'] = i['item_group']
        row["opening_qty"] = row["opening_qty"] + i["opening_qty"]
        row["opening_val"] = row["opening_val"] + i["opening_val"]
        row["in_qty"] = row["in_qty"] + i["in_qty"]
        row["in_val"] = row["in_val"] + i["in_val"]
        row["out_qty"] = row["out_qty"] + i["out_qty"]
        row["out_val"] = row["out_val"] + i["out_val"]
        row["sales_out_qty"] = row["sales_out_qty"] + i["sales_out_qty"]
        row["sales_in_qty"] = row["sales_in_qty"] + i["sales_in_qty"]
        row["sales_out_val"] = row["sales_out_val"] + i["sales_out_val"]
        row["sales_in_val"] = row["sales_in_val"] + i["sales_in_val"]
        row["bal_qty"] = row["bal_qty"] + i["bal_qty"]
        row["bal_val"] = row["bal_val"] + i["bal_val"]
    
    return group_by_data


def get_columns(filters):
    """return columns"""
    
    if(filters.get("group_by") == "Warehouse"):        
        group_by_lable = "Warehouse"
        group_by_field = "warehouse"
    elif(filters.get("group_by") == "Item Group"):
        group_by_lable = "Item Group"
        group_by_field = "item_group"
    elif(filters.get("group_by") == "Supplier"):
        group_by_lable = "Supplier"
        group_by_field = "n_supplier"
    elif(filters.get("group_by") == "Item"):
        group_by_lable = "Item"
        group_by_field = "item_code"   
 
    
    columns = [{"label": _(group_by_lable), "fieldname": group_by_field,"fieldtype": "Link", "options": group_by_lable, "width": 170}]
    if filters.get('group_by') == "Item":
        columns.append({"label": _('Item Name'), "fieldname": "item_name","fieldtype": "Data", "width": 100})
        columns.append({"label": _('Item Group'), "fieldname": "item_group","fieldtype": "Data", "width": 100})
    columns.append({"label": _("Balance Qty"), "fieldname": "bal_qty","fieldtype": "Float", "width": 100, "convertible": "qty"})
    columns.append({"label": _("Balance Value"), "fieldname": "bal_val","fieldtype": "Currency", "width": 100})
    columns.append({"label": _("Opening Qty"), "fieldname": "opening_qty","fieldtype": "Float", "width": 100, "convertible": "qty"})
    columns.append({"label": _("Opening Value"), "fieldname": "opening_val","fieldtype": "Float", "width": 110})
    columns.append({"label": _("In Qty"), "fieldname": "in_qty","fieldtype": "Float", "width": 80, "convertible": "qty"})
    columns.append({"label": _("In Value"), "fieldname": "in_val","fieldtype": "Float", "width": 80})
    columns.append({"label": _("Out Qty"), "fieldname": "out_qty","fieldtype": "Float", "width": 80, "convertible": "qty"})
    columns.append({"label": _("Out Value"), "fieldname": "out_val","fieldtype": "Float", "width": 80})
    columns.append({"label": _("In Sales Qty"), "fieldname": "sales_in_qty","fieldtype": "Float", "width": 100, "convertible": "qty"})
    columns.append({"label": _("In Sales Value"), "fieldname": "sales_in_val","fieldtype": "Float", "width": 150})
    columns.append({"label": _("Out Sales Qty"), "fieldname": "sales_out_qty","fieldtype": "Float", "width": 100, "convertible": "qty"})
    columns.append({"label": _("Out Sales Value"), "fieldname": "sales_out_val", "fieldtype": "Float", "width": 150})


    return columns

def get_group_by(by):
    if(by == "Warehouse"):        
        return "warehouse"
    elif(by == "Item Group"):
        return "item_group"
    elif(by == "Supplier"):
        return "n_supplier"
    elif(by == "Item"):
        return "item_code"
        
def get_or_make_row(group_by_data, group_by, by):
    for i in group_by_data:
        if(i[group_by] == by):
            return i
    row = {
        group_by: by,
        "opening_qty": 0.0,
        "opening_val": 0.0,
        "in_qty": 0.0,
        "in_val": 0.0,
        "out_qty": 0.0,
        "out_val": 0.0,
        "bal_qty": 0.0,
        "bal_val": 0.0,
        "sales_in_qty":0.0,
        "sales_out_qty":0.0,
        "sales_in_val":0.0,
        "sales_out_val":0.0
        }
    group_by_data.append(row)
    return row

def get_conditions(filters):
    conditions = ""
    if not filters.get("from_date"):
        frappe.throw(_("'From Date' is required"))

    if filters.get("to_date"):
        conditions += " and sle.posting_date <= %s" % frappe.db.escape(
            filters.get("to_date"))
    else:
        frappe.throw(_("'To Date' is required"))

    if filters.get("company"):
        conditions += " and sle.company = %s" % frappe.db.escape(
            filters.get("company"))

    if filters.get("warehouse"):
        warehouse_list = format_in_sql_statment(filters.get('warehouse'))
        conditions+= "and warehouse in({})".format(warehouse_list)

    if filters.get("warehouse_type") and not filters.get("warehouse"):
        conditions += " and exists (select name from `tabWarehouse` wh \
			where wh.warehouse_type = '%s' and sle.warehouse = wh.name)" % (filters.get("warehouse_type"))
            
    if filters.get('get_item_from'):
        item_code_list = get_item_code_in_purchase_invoice(filters)
        conditions+=" and sle.item_code in({0})".format(item_code_list)
    # if filters.get('')       
    return conditions


def get_stock_ledger_entries(filters, items):
    item_conditions_sql = ''
    if not filters.get('get_item_from'):
        if items:
            item_conditions_sql = ' and sle.item_code in ({})'\
                .format(', '.join([frappe.db.escape(i, percent=False) for i in items]))

    conditions = get_conditions(filters)

    return frappe.db.sql("""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
			sle.item_code as name, sle.voucher_no
		from
			`tabStock Ledger Entry` sle force index (posting_sort_index)
		where sle.docstatus < 2  %s %s 
		order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty""" %  # nosec
                         (item_conditions_sql, conditions), as_dict=1)


def get_item_warehouse_map(filters, sle):
    iwb_map = {}
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    float_precision = cint(frappe.db.get_default("float_precision")) or 3

    for d in sle:
        key = (d.company, d.item_code, d.warehouse)
        if key not in iwb_map:
            iwb_map[key] = frappe._dict({
                "opening_qty": 0.0, "opening_val": 0.0,
                "in_qty": 0.0, "in_val": 0.0,
                "out_qty": 0.0, "out_val": 0.0,
                "bal_qty": 0.0, "bal_val": 0.0,
                "sales_in_qty": 0.0,"sales_in_val": 0.0, 
                "sales_out_qty": 0.0,"sales_out_val": 0.0, 
            })

        qty_dict = iwb_map[(d.company, d.item_code, d.warehouse)]

        if d.voucher_type == "Stock Reconciliation":
            qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
        else:
            qty_diff = flt(d.actual_qty)

        value_diff = flt(d.stock_value_difference)

        if d.posting_date < from_date:
            qty_dict.opening_qty += qty_diff
            qty_dict.opening_val += value_diff

        elif d.posting_date >= from_date and d.posting_date <= to_date:
            if d.voucher_type != "Sales Invoice":
                if flt(qty_diff, float_precision) >= 0:
                    qty_dict.in_qty += qty_diff
                    qty_dict.in_val += value_diff
                else:
                    qty_dict.out_qty += abs(qty_diff)
                    qty_dict.out_val += abs(value_diff)
            else:
                if flt(qty_diff, float_precision) >= 0:
                    qty_dict.sales_in_qty += qty_diff
                    qty_dict.sales_in_val += value_diff
                else:
                    qty_dict.sales_out_qty += abs(qty_diff)
                    qty_dict.sales_out_val += abs(value_diff)

        qty_dict.val_rate = d.valuation_rate
        qty_dict.bal_qty += qty_diff
        qty_dict.bal_val += value_diff

    iwb_map = filter_items_with_no_transactions(iwb_map, float_precision)

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


def get_items(filters):
    conditions = []
    if filters.get("item_code"):
        conditions.append("item.name=%(item_code)s")
    else:
        if filters.get("supplier"):
            conditions.append("item.n_supplier='{}'".format(filters.get("supplier")))
        if filters.get("item_group"):
            item_group_list = format_in_sql_statment(filters.get('item_group'))
            conditions.append("item_group in({0})".format(item_group_list))

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
			item.name, item.item_code, item.description, item.item_group, item.n_supplier, item.brand, item.stock_uom %s
		from
			`tabItem` item
			%s
		where
			item.name in (%s)
	""" % (cf_field, cf_join, ','.join(['%s'] * len(items))), items, as_dict=1)

    for item in res:
        item_details.setdefault(item.name, item)

    return item_details

def get_item_name_from_item_code(item_code):
    data = frappe.db.sql("""select item_name from `tabItem` item where item_code = '{}'""".format(item_code), as_dict=1)
    return data[0].item_name


def validate_filters(filters):
    if not (filters.get("warehouse")):
        sle_count = flt(frappe.db.sql(
            """select count(name) from `tabStock Ledger Entry`""")[0][0])
        if sle_count > 500000:
            frappe.throw(
                _("Please set filter based on Warehouse due to a large amount of entries."))

def get_item_code_in_purchase_invoice(filters):
    sql_conditions = ""
    if filters.get('supplier'):
        sql_conditions+= " and pui.supplier like '{}'".format(filters.get('supplier'))
    purchase_invoice_list = ''
    item_code_list = [] 
    purchase_invoice_list = format_in_sql_statment(filters.get('get_item_from'))
    data = frappe.db.sql(""" select puii.item_code from `tabPurchase Invoice Item` puii, `tabPurchase Invoice` pui
              where pui.name = puii.parent {0} and pui.name in ({1})""".format(sql_conditions,purchase_invoice_list),as_dict=1)
    for item in data:
        item_code_list.append(item.item_code)

    final_output = format_in_sql_statment(item_code_list)

    return final_output
           


def format_in_sql_statment(the_list):
    output_string = ''
    for item in the_list:
        output_string+="'"+item+"',"
    output_string = output_string[0:len(output_string) - 1]
    return output_string  
  
@frappe.whitelist()
def get_purhcase_invoice(doctype = None,filters=None):
    value = json.loads(filters)
    # posting_date = format_in_sql_statment(value['posting_date'][1])
    from_date = value["from_date"]
    to_date = value["to_date"]
    supplier = value['supplier'] if "supplier" in value else ''
    sql = ''
    if supplier != '':
        # sql = "select name,title,posting_date from `tabPurchase Invoice` where supplier like '{0}' and posting_date in({1})".format(supplier,posting_date)
        sql = "select name,title,posting_date from `tabPurchase Invoice` where supplier like '{0}' and posting_date between '{1}' and '{2}' and status not in ('Draft','Return','Cancelled')".format(supplier,from_date,to_date)
    else:
        # sql = "select name,title,posting_date from `tabPurchase Invoice` where posting_date in({0})".format(posting_date)
        sql = "select name,title,posting_date from `tabPurchase Invoice` where posting_date between '{0}' and '{1}' and status not in ('Draft','Return','Cancelled')".format(from_date,to_date)
    return frappe.db.sql(sql,as_dict=1)

@frappe.whitelist()
def get_item_group(doctype = None):      
    return frappe.db.sql( """select name from `tabItem Group` where name not like 'All Item Groups'""",as_dict=1)

@frappe.whitelist()
def get_warehouse_data(doctype = None):      
    return frappe.db.sql("""select ifnull(name,'') as name from `tabWarehouse` where name not like '' """,as_dict=1)
