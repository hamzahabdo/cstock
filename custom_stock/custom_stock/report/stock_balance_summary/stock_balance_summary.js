// Copyright (c) 2016, burjalmaha.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Balance Summary"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "MultiSelectList",
			"width": "80",
			get_data: () => {
				return get_warehouse_data()
			}
		},
		{
			"fieldname": "warehouse_type",
			"label": __("Warehouse Type"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Warehouse Type"
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Supplier",
			on_change:function(){
				frappe.query_report.filters.forEach(filter=>{
					if(filter.fieldname ==  "get_item_from"){
						filter._selected_values = []
						filter.values = []
					}
				});
			}
		},
		{
			"fieldname":"get_item_from",
			"label": __("Get Item From"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				if (!frappe.query_report.filters) return;
				
				return get_item_from_data()
			},
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "MultiSelectList",
			"width": "80",
			get_data: function(txt) {
				if (!frappe.query_report.filters) return;
				
				return get_item_group_data()
			},
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query",
				};
			}
		},
		{
			"fieldname": "group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"width": "80",
			"options": ["Warehouse", "Item Group", "Supplier","Item"],
			"default": "Warehouse"
		},
		{
			"fieldname": "select_all_invoices",
			"label": __("Select All Invoices"),
			"fieldtype": "Check",
			"width": "10",
			on_change:function(){
				const get_item_from = document.querySelector('[data-fieldname="get_item_from"]')
				if(frappe.query_report.get_filter_value('select_all_invoices') == 1){
					frappe.query_report.filters.forEach(filter=>{
						if(filter.fieldname == 'get_item_from'){
							console.log(filter)
							filter._options.forEach(option=>{
								filter._selected_values.push(option)
								filter.values.push(option.value)
							})
							get_item_from.querySelector('.status-text').textContent = filter._selected_values.length+" values selected";
						}
					});
				}else{
					frappe.query_report.filters.forEach(filter=>{
						if(filter.fieldname == 'get_item_from'){
							// console.log(filter)
							filter._options.forEach(option=>{
								filter._selected_values = []
								filter.values = []
							})
							get_item_from.querySelector('.status-text').textContent = "";
						}
					});
				}
			}
		},
		{
			"fieldname": "s_warehouse",
			"label": __("Warehouse"),
			"fieldtype": "MultiSelectList",
			"width": "80",
			get_data: () => {
				return get_warehouse_data()
			}
		},
		{
			"fieldname": "com",
			"label": __("Operator"),
			"fieldtype": "Select",
			"width": "80",
			"options": [__("Greater Than"), __("Equal")],
			"default": __("Greater Than")
		},
		{
			"fieldname": "qty",
			"label": __("Qty"),
			"fieldtype": "Data",
			"width": "80"
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

function convert(timestamp) {
	var date = new Date(timestamp);
	return [date.getFullYear(),("0" + (date.getMonth()+1)).slice(-2),("0" + date.getDate()).slice(-2),].join('-');
}


function listDate(startDate,endDate){
	var listDate = [];
	var dateMove = new Date(startDate);
	var strDate = startDate;

	while (strDate <= endDate){
	  var strDate = dateMove.toISOString().slice(0,10);
	  listDate.push(strDate);
	  dateMove.setDate(dateMove.getDate()+1);
	};
	return listDate
}
async function get_item_from_data(){
	let data = [];
	let supplier = frappe.query_report.get_filter_value('supplier');
	let purchase_invoice_list = null;
	let from_date = frappe.query_report.get_filter_value('from_date')
	let to_date = frappe.query_report.get_filter_value('to_date')
	let date_list = listDate(convert(from_date),convert(to_date));
	let args = {}
	date_list.pop()
	if(!supplier){
		args = {
			doctype: 'Purchase Invoice',
			filters:{
				// "posting_date":["in", date_list],
				"from_date":from_date,
				"to_date":to_date				
			}
		}
	}else{
		args = {
			doctype: 'Purchase Invoice',
			filters: {
				"supplier":supplier,
				// "posting_date":["in", date_list],
				"from_date":from_date,
				"to_date":to_date	
			}
		}
	}
	frappe.call({
		type: "GET",
		method:'custom_stock.custom_stock.report.stock_balance_summary.stock_balance_summary.get_purhcase_invoice',
		async: false,
		no_spinner: true,
		args: args,
		callback: function(r) {
			purchase_invoice_list = r.message;
		}
	});
	purchase_invoice_list.forEach(invoice=>{
		data.push({'value':invoice.name,'description':invoice.title+"  "+invoice.posting_date});
	})
	return data;
}
async function get_item_group_data(){
	let data = [];
	let response = await frappe.call({
		type: "GET",
		method:'custom_stock.custom_stock.report.stock_balance_summary.stock_balance_summary.get_item_group',
		no_spinner: true,
		args: {
			doctype: 'Item Group'
		}
	});

	response.message.forEach(item=>{
		data.push({'value':item.name,'description':''});
	})
	return data;
}
async function get_warehouse_data(){
	let data = [];
	let response = await frappe.call({
						type: "GET",
						method:'custom_stock.custom_stock.report.stock_balance_summary.stock_balance_summary.get_warehouse_data',
						async:true,
						no_spinner: true,
						args: {
							doctype: 'Stock Ledger Entry'
						}
				});		
	response.message.forEach(warehouse=>{
		data.push({'value':warehouse.name,'description':''});
	})
	return data;
}