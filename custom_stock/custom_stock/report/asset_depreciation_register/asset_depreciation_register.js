// Copyright (c) 2016, BM and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Asset Depreciation Register"] = {
	"filters": [
		{
			"fieldname": "asset_name",
			"label": __("Asset Name"),
			"fieldtype": "Link",
			"options": "Asset"
		},
		{
			"fieldname": "location_name",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location"
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname": "schedule_date",
			"label": __("Schedule Date"),
			"fieldtype": "Date Range"
		}


	]
};
