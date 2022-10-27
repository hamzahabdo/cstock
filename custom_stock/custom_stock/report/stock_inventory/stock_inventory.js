// Copyright (c) 2016, BM and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Inventory"] = {
	"filters": [
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
		},
		{
			"fieldname": "inventory_voucher",
			"label": __("Inventory Voucher"),
			"fieldtype": "Link",
			"options": "Stock Inventory Processing",
			"reqd": 1,
			"get_query": function () {
				let warehouse = frappe.query_report.get_filter_value("warehouse");
				let filters = {
					"docstatus": 1
				}
				if (warehouse) {
					filters.warehouse = warehouse;
				}
				return { "filters": filters }
			}
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "MultiSelectList",
			get_data: function (txt) {
				if (!frappe.query_report.filters) return;
				let inventory_voucher = frappe.query_report.get_filter_value("inventory_voucher");
				// let filters = frappe.db.get_doc("Stock Inventory Processing", inventory_voucher).then((r) => {
				// 	console.log(r);
				// 	// if (r.item_group != null) {
				// 	// return frappe.db.get_link_options("Item Group", txt, { name: r.item_group });
				// 	// } else {
				// 	// return frappe.db.get_link_options("Item Group", txt);
				// 	// }
				// });
				// console.log(filters);
				if (!inventory_voucher) return;
				return frappe.db.get_link_options("Item Group", txt);
			}
		},
		{
			"fieldname": "not_in_item_group",
			"label": __("Not in Item Group"),
			"fieldtype": "MultiSelectList",
			get_data: function (txt) {
				if (!frappe.query_report.filters) return;
				let inventory_voucher = frappe.query_report.get_filter_value("inventory_voucher");
				if (!inventory_voucher) return;
				return frappe.db.get_link_options("Item Group", txt);
			}
		},
		{
			"fieldname": "inventory_type",
			"label": __("Inventory Type"),
			"fieldtype": "MultiSelectList",
			get_data: function (txt) {
				if (!frappe.query_report.filters) return;
				let inventory_voucher = frappe.query_report.get_filter_value("inventory_voucher");
				if (!inventory_voucher) return;
				let types = [
					{ value: __("Deficit"), description: __("Loss in stock") },
					{ value: __("Surplus"), description: __("Gain in stock") },
					{ value: __("Uninventorized"), description: __("Uninventorized Items") }
				]
				return types;
			}
		}
	]
};
