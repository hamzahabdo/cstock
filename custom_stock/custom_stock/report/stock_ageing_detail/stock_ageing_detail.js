// Copyright (c) 2016, burjalmaha.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Ageing Detail"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			get_query: () => {
				var warehouse_type = frappe.query_report.get_filter_value('warehouse_type');
				if (warehouse_type) {
					return {
						filters: {
							'warehouse_type': warehouse_type
						}
					};
				}
			}
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function () {
				return {
					query: "erpnext.controllers.queries.item_query",
				};
			}
		},
		{
			"fieldname": "from_date0",
			"label": __("From Date 1"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.year_start()
		},
		{
			"fieldname": "to_date0",
			"label": __("To Date 1"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_days(frappe.datetime.add_months(frappe.datetime.year_start(), 3), -1)
		},
		{
			"fieldname": "from_date1",
			"label": __("From Date 2"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.year_start(), 3)
		},
		{
			"fieldname": "to_date1",
			"label": __("To Date 2"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_days(frappe.datetime.add_months(frappe.datetime.year_start(), 6), -1)
		},
		{
			"fieldname": "from_date2",
			"label": __("From Date 3"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.year_start(), 6)
		},
		{
			"fieldname": "to_date2",
			"label": __("To Date 3"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_days(frappe.datetime.add_months(frappe.datetime.year_start(), 9), -1)
		},
		{
			"fieldname": "from_date3",
			"label": __("From Date 4"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.year_start(), 9)
		},
		{
			"fieldname": "to_date3",
			"label": __("To Date 4"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.year_end()
		}
	],

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "out_qty" && data && data.out_qty > 0) {
			value = "<span style='color:red'>" + value + "</span>";
		}
		else if (column.fieldname == "in_qty" && data && data.in_qty > 0) {
			value = "<span style='color:green'>" + value + "</span>";
		}

		return value;
	}
};
