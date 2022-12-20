# Copyright (c) 2013, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    columns = [
        {
            "fieldname": "asset",
            "label": _("Asset"),
            "fieldtype": "Link",
            "options": "Asset"
        },
        {
            "fieldname": "asset_name",
            "label": _("Asset Name"),
            "fieldtype": "Data",
        },
        {
            "fieldname": "location",
            "label": _("Location"),
            "fieldtype": "Link",
            "options": "Location"
        },
        {
            "fieldname": "branch",
            "label": _("Branch"),
            "fieldtype": "Link",
            "options": "Branch"
        },
        {
            "fieldname": "gross_purchase_amount",
            "label": _("Gross Purchase Amount"),
            "fieldtype": "Currency",
        },
        {
            "fieldname": "purchase_date",
            "label": _("Purchase Date"),
            "fieldtype": "Date",
        },
        {
            "fieldname": "available_for_use_date",
            "label": _("Available For Use Date"),
            "fieldtype": "Date",
        },
        {
            "fieldname": "opening_accumulated_depreciation",
            "label": _("Opening Accumulated Depreciation"),
            "fieldtype": "Currency",
        },
        {
            "fieldname": "period_start_accumulated_depreciation",
            "label": _("Period Start Accumulated Depreciation"),
            "fieldtype": "Currency",
        },
        {
            "fieldname": "period_depreciation_amount",
            "label": _("Period Depreciation Amount"),
            "fieldtype": "Currency",
        },
        {
            "fieldname": "depreciation_amount",
            "label": _("Depreciation Amount"),
            "fieldtype": "Currency",
        },
        {
            "fieldname": "accumulated_depreciation_amount",
            "label": _("Accumulated Depreciation Amount"),
            "fieldtype": "Currency",
        },
        {
            "fieldname": "asset_value",
            "label": _("Asset Value"),
            "fieldtype": "Currency",
        }

    ]
    return columns


def get_conditions(filters):
    conditions = " "
    asset = filters.get("asset_name")
    location = filters.get("location_name")
    branch = filters.get("branch")
    from_to_date = filters.get("schedule_date")

    if asset:
        conditions += " and ast.name = '{}'".format(asset)

    if location:
        conditions += " and ast.location = '{}'".format(location)

    if branch:
        conditions += " and ast.branch = '{}'".format(branch)

    if from_to_date:
        conditions += " and ds.schedule_date between '{0}' and '{1}'".format(
            from_to_date[0], from_to_date[1])

    return conditions


def get_data(filters):
    sql_statment = """
    select
    	ast.asset_name ,
        ast.name as asset,
		ast.location ,
		ast.branch ,
        ast.gross_purchase_amount ,
		ast.purchase_date ,
		ast.available_for_use_date ,
		ds.schedule_date ,
        ast.opening_accumulated_depreciation ,
		((max(ds.accumulated_depreciation_amount)) - (sum(ds.depreciation_amount)))as period_start_accumulated_depreciation,
    	sum(ds.depreciation_amount)as period_depreciation_amount,
     	ds.depreciation_amount ,
        max(ds.accumulated_depreciation_amount)as accumulated_depreciation_amount ,
        (ast.gross_purchase_amount - (max(ds.accumulated_depreciation_amount))) as asset_value
    from
    	`tabAsset` ast ,`tabDepreciation Schedule` ds
    where
    	ast.name = ds.parent
        and ast.docstatus = 1
        and ds.journal_entry IS NOT NULL
    	{}
    group by ast.name
    """.format(get_conditions(filters))

    data = frappe.db.sql(sql_statment, as_dict=1)

    sql_statment_undepreciated_assets = """
    select
        ast.asset_name ,
        ast.name as asset,
		ast.location ,
		ast.branch ,
        ast.gross_purchase_amount ,
		ast.purchase_date ,
		ast.available_for_use_date ,
		ds.schedule_date ,
        ast.opening_accumulated_depreciation ,
		((max(ds.accumulated_depreciation_amount)) - (sum(ds.depreciation_amount)))as period_start_accumulated_depreciation,
    	sum(ds.depreciation_amount)as period_depreciation_amount,
     	'0' as depreciation_amount ,
        '0' as accumulated_depreciation_amount ,
        ast.gross_purchase_amount as asset_value
    from
        `tabAsset` ast ,`tabDepreciation Schedule` ds
    where
        ast.name = ds.parent
        and ast.docstatus = 1
        and ast.name != ALL (select
    	distinct ast.name 
    from
    	`tabAsset` ast ,`tabDepreciation Schedule` ds
    where
    	ast.name = ds.parent
        and ds.journal_entry IS NOT NULL)
        {}
    group by ast.name
    """.format(get_conditions(filters))

    undepreciated_assets = frappe.db.sql(sql_statment_undepreciated_assets, as_dict=1)
    data.extend(undepreciated_assets)

    return data
