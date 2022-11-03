frappe.ui.form.on('Stock Reconciliation', {
	refresh(frm) {
		frm.set_df_property("branch", "read_only", 1);
		if (frm.doc.docstatus < 1 && frm.doc.purpose == "Stock Reconciliation") {
			frm.add_custom_button(__("Fetch Items to Reconciliate"), function () {
				frm.events.get_negative_items(frm);
			});
			if (frm.doc.warehouse) {
				frm.add_custom_button(__("Fetch inventory items"), function () {
					frm.events.get_inventory_items(frm);
				});
			}
			if (frm.doc.purpose == "Stock Reconciliation") {
				if (frm.doc.items != undefined) {
					if (frm.doc.items.length > 0) {
						if (frm.doc.items[0].item_code != undefined) {
							frm.add_custom_button(__("Reconciliate"), function () {
								frm.events.reconciliate_items(frm);
							});
						}
					}
				}
			}
		}
	},
	purpose(frm) {
		if (frm.doc.purpose != "Stock Reconciliation") {
			frm.set_df_property("warehouse", "read_only", 0);
		}
		else {
			frm.events.empty_table(frm, "items");
		}
		frm.refresh();
	},
	warehouse(frm) {
		if (!frm.doc.warehouse) {
			frm.events.empty_table(frm, "items");
		}
		frm.events.update_items_details(frm);
	},
	posting_date(frm) {
		if (!frm.doc.warehouse) {
			frm.events.empty_table(frm, "items");
		}
		frm.events.update_items_details(frm);
	},
	posting_time(frm) {
		if (!frm.doc.warehouse) {
			frm.events.empty_table(frm, "items");
		}
		frm.events.update_items_details(frm);
	},
	reconciliate_items: function (frm) {
		if (frm.doc.items != undefined) {
			if (frm.doc.items[0].item_code != undefined) {
				frm.doc.items.forEach(item => {
					item.qty = 0;
				});
				frm.refresh_field("items");
			}
		}

	},
	get_negative_items: function (frm) {
		frappe.prompt({
			label: "Warehouse", fieldname: "warehouse", fieldtype: "Link", options: "Warehouse", reqd: 1,
			"get_query": function () {
				return {
					"filters": {
						"company": frm.doc.company,
					}
				}
			}
		},
			function (data) {
				let args = {
					warehouse: data.warehouse
				};

				frm.events.get_reconciliation_items(frm, args, "get_negative_items");
				// frappe.call({
				// 	method: "nct.common.stock_common.get_negative_items",
				// 	args: {
				// 		warehouse: data.warehouse,
				// 		posting_date: frm.doc.posting_date,
				// 		posting_time: frm.doc.posting_time,
				// 		company: frm.doc.company
				// 	},
				// 	callback: function (r) {
				// 		console.log(r.message);
				// 		var items = [];
				// 		frm.clear_table("items");
				// 		for (var i = 0; i < r.message.length; i++) {
				// 			var d = frm.add_child("items");
				// 			$.extend(d, r.message[i]);
				// 			if (!d.qty) d.qty = null;
				// 			if (!d.valuation_rate) d.valuation_rate = null;
				// 		}
				// 		frm.refresh_field("items");
				// 	}
				// });
				// frm.refresh();
			}
			, __("Get Items"), __("Update"));
	},
	get_inventory_items: function (frm) {
		const fields = [
			{
				label: "Stock Inventory Processing Document", fieldname: "sip",
				fieldtype: "Link", options: "Stock Inventory Processing", reqd: 1,
				"get_query": function () {
					return {
						"filters": {
							"docstatus": 1,
							"warehouse": frm.doc.warehouse
						}
					}
				}
			},
			{
				label: "Items Type", fieldname: "items_type", fieldtype: "Select",
				options: ["All", "Positive", "Negative"], reqd: 1, default: "All"
			},
		];
		frappe.prompt(fields,
			function (data) {
				frappe.db.get_doc("Stock Inventory Processing", data.sip).then((r) => {
					if (r.docstatus != 1) {
						frappe.throw(__("You have selected an invalid documnet!"));
					}
				})
					.then(() => {
						let qty;
						if (data.item_type == __("All")) {
							qty = 0;
						}
						else if (data.item_type == __("Positive")) {
							qty = 1;
						}
						else {
							qty = -1;
						}


						let args = {
							warehouse: frm.doc.warehouse,
							inventory: data.sip,
							qty: qty
						};

						frm.events.get_reconciliation_items(frm, args, "get_inventory_items");
						frm.set_df_property("warehouse", "read_only", 1);
					});

			}
			, __("Get Items"), __("Update"));

	},
	get_reconciliation_items: function (frm, args, method) {
		frappe.call({
			method: "custom_stock.common.stock_common." + method,
			args: args,
			callback: function (r) {
				if (r && r.message.length > 0) {
					// console.log(r.message);
					// var items = [];
					frm.clear_table("items");
					for (var i = 0; i < r.message.length; i++) {
						var d = frm.add_child("items");
						$.extend(d, r.message[i]);
						if (!d.qty) d.qty = null;
						if (!d.valuation_rate) d.valuation_rate = null;
					}
					frm.refresh_field("items");
				}
				else {
					frm.events.empty_table(frm, "items");
					frappe.throw(__("No items were found to reconciliate!"));
				}
			}
		});
		frm.refresh();
	},
	empty_table: function (frm, table) {
		frm.clear_table(table);
		frm.refresh_field(table);
	},
	set_warehouse_and_qty(frm) {
		frm.doc.items.forEach(item => {
			item.warehouse = frm.doc.warehouse;
			item.qty += item.reconciliated_qty;
		});
		frm.refresh_field("items");
	},
	update_items_details(frm) {
		if (frm.doc.warehouse) {
			for (const item of frm.doc.items) {
				frm.events.updae_current_item(frm, item)
			}
		}
	},
	updae_current_item(frm, item) {
		let cdt = item.doctype,
			cdn = item.name;
		let d = frappe.model.get_doc(cdt, cdn);
		if (d.item_code) {
			frappe.call({
				method: "erpnext.stock.doctype.stock_reconciliation.stock_reconciliation.get_stock_balance_for",
				args: {
					item_code: d.item_code,
					warehouse: frm.doc.warehouse,
					posting_date: frm.doc.posting_date,
					posting_time: frm.doc.posting_time,
					batch_no: d.batch_no
				},
				callback: function (r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "qty", r.message.qty);
						frappe.model.set_value(cdt, cdn, "valuation_rate", r.message.rate);
						frappe.model.set_value(cdt, cdn, "current_qty", r.message.qty);
						frappe.model.set_value(cdt, cdn, "current_valuation_rate", r.message.rate);
						frappe.model.set_value(cdt, cdn, "current_amount", r.message.rate * r.message.qty);
						frappe.model.set_value(cdt, cdn, "amount", r.message.rate * r.message.qty);
						frappe.model.set_value(cdt, cdn, "current_serial_no", r.message.serial_nos);
					}
					else {
						frappe.throw(__("Item does not exist in this warehouse!"));
					}
				}
			});
		}
	},
	validate_amount_difference(frm) {
		let amount_difference = 0;
		for (const item of frm.doc.items) {
			amount_difference += item.amount_difference;
		}
		if ( amount_difference.toFixed(4) != frm.doc.difference_amount.toFixed(4)) {
			frappe.throw(__("Difference amount is not properly set!"));
		}
	},
	before_submit(frm) {
		frm.events.validate_amount_difference(frm);
	}
})
var _tmp = 0;
frappe.ui.form.on('Stock Reconciliation Item', {
	items_add(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, 'warehouse', frm.doc.warehouse);

		// set_warehouse(frm);
	},
	reconciliated_qty(frm, cdt, cdn) {
		let item = locals[cdt][cdn];
		// frm.events.updae_current_item(frm, item);
		frappe.model.set_value(cdt, cdn, 'qty', item.current_qty + item.reconciliated_qty);



		// if (frm.meta.is_submittable
		// 	&& frm.perm[0] && frm.perm[0].submit
		// 	&& !frm.is_dirty()
		// 	&& !frm.is_new()
		// 	&& !frappe.model.has_workflow(frm.doctype) // show only if no workflow
		// 	&& frm.doc.docstatus === 0) {
		// 	console.log("wwomeeeeeeee");
		// 	let item = locals[cdt][cdn];
		// 	let index = frm.doc.taxes.indexOf(item);
		// 	frm.doc.items.splice(index, 1);
		// }

		// console.log(_tmp);
		// frappe.model.set_value(cdt, cdn, 'qty', _tmp).then(() => {
		// 	frappe.model.set_value(cdt, cdn, 'qty', (qty_tmp + item.reconciliated_qty)).then(() => {
		// 		_tmp = item.qty - item.reconciliated_qty;
		// 	});
		// });

	}
})

function set_warehouse(frm) {
	frm.doc.items.forEach(item => {
		item.warehouse = frm.doc.warehouse;
	});
	frm.refresh_field("items");
}