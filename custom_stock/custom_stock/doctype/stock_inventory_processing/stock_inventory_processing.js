// Copyright (c) 2020, BM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Inventory Processing', {
	setup: function (frm) {
		frm.docs_found = [];
		frm.docs_removed_doc;
		frm.groups_found = [];
		frm.groups_removed_doc;

		frm.set_query("document_name", "stock_inventory_documents", function (doc) {
			return {
				filters: {
					"docstatus": 0,
					"warehouse": doc.warehouse
				}
			};
		});

		frm.set_query("item_group", function (doc) {
			return {
				filters: {
					"is_group": 0
				}
			};
		});
	},
	refresh: function (frm) {
		frm.fields_dict["warehouse"].set_focus();
		frm.fields_dict["stock_inventory_documents"].grid.add_custom_button(__("Get Items"),
			() => {
				frm.events.get_inventory_items(frm);
			});

	},
	get_inventory_items(frm) {
		nct.utils.empty_table(frm, "items");
		if (frm.doc.warehouse) {

			// if (frm.doc.stock_inventory_documents[0].document_name != undefined) {
			let docs_list = nct.utils.get_child_table_elements(frm, "stock_inventory_documents", "document_name"),
				docs_string;

			if (docs_list.length != 0) {

				docs_string = nct.utils.array_to_db_string(docs_list);

				let args = {
					warehouse: frm.doc.warehouse,
					docs: docs_string,
				}

				if (frm.doc.all_items) {
					args.all_items = frm.doc.all_items;
					let groups_list = nct.utils.get_child_table_elements(frm, "item_groups", "item_group"),
						groups_string;
					if (groups_list.length != 0) {
						groups_string = nct.utils.array_to_db_string(groups_list);
						args.item_groups = groups_string;
					}
					// if (frm.doc.item_groups != undefined) {
					// 	if (frm.doc.item_groups.length > 0) {
					// 		if (frm.doc.item_groups[0].item_group != undefined) {
					// 			console.log(frm.doc.item_groups);
					// 			args.item_groups = frm.doc.item_group;
					// 		}
					// 	}
					// }
				}
				console.log(args);
				// if (_args) {
				// 	args = { ...args, ..._args };
				// }

				frm.call({
					method: "get_inventory_items",
					freeze: true,
					args: args,
					callback: (r) => {
						if (r && r.message) {
							let items = r.message;
							for (const key in items) {
								if (items.hasOwnProperty(key)) {
									const item = items[key];
									let diff_qty = (item.qty - item.a_qty),
										total = (item.rate * diff_qty);
									frm.add_child("items", {
										item_code: item.item_code,
										item_name: item.item_name,
										item_group: item.item_group,
										actual_qty: item.a_qty,
										inventory_qty: item.qty,
										difference_qty: diff_qty,
										rate: item.rate,
										amount: total
									});
								}
							}
							frm.refresh_field("items");
						}
					}
				});
			}
			// }
		}
		else {
			nct.utils.empty_table(frm, "items");
		}

	},
	// empty_table(frm, table) {
	// 	frm.clear_table(table);
	// 	frm.refresh_field(table);
	// },
	// add_empty_row(frm, table) {
	// 	frm.add_child(table);
	// 	frm.refresh_field(table);
	// }
});

nct.utils.check_child_table_duplicates('Stock Inventory Document', 'stock_inventory_documents', 'document_name', 'docs_found', 'docs_removed_doc', 'get_inventory_items', 'items');
nct.utils.check_child_table_duplicates('Stock Inventory Processing Item Group', 'item_groups', 'item_group', 'groups_found', 'groups_removed_doc');

// frappe.ui.form.on('Stock Inventory Document', {
// 	['document_name']: function (frm, cdt, cdn) {
// 		console.log("wooooooooooooooooooooooooow");
// 		let d = locals[cdt][cdn];
// 		let status = true;

// 		if (!frm.doc.warehouse || d.document_name == undefined) {
// 			status = false;
// 			frm.doc.stock_inventory_documents.splice((d.idx) - 1, 1);
// 			nct.utils.add_empty_row(frm, "stock_inventory_documents");
// 			if (d.document_name) {
// 				frappe.throw(__("Please select a warehouse first"));
// 			}
// 		}
// 		for (const document of frm.found) {
// 			if (d.document_name == document || d.document_name == undefined) {
// 				frm.doc.stock_inventory_documents.splice((d.idx) - 1, 1);
// 				nct.utils.add_empty_row(frm, "stock_inventory_documents");
// 				frm.refresh();
// 				status = false;
// 			}
// 		}
// 		if (status == true) {
// 			nct.utils.add_empty_row(frm, "stock_inventory_documents");
// 			frm.found.push(d.document_name);
// 		}
// 	},
// 	['before_stock_inventory_documents_remove']: function (frm, cdt, cdn) {
// 		let d = locals[cdt][cdn];

// 		frm.removed_doc = d;
// 		frm.found.splice((d.idx) - 1, 1);
// 		frm.refresh();

// 	},
// 	['stock_inventory_documents_remove']: function (frm, cdt, cdn) {
// 		if (frm.removed_doc.document_name) {
// 			frm.events.get_inventory_items(frm);
// 		}
// 		if (frm.doc.stock_inventory_documents.length == 0) {
// 			nct.utils.empty_table(frm, "items");
// 			nct.utils.add_empty_row(frm, "stock_inventory_documents");
// 			nct.utils.add_empty_row(frm, "items");
// 		}
// 	}
// });
