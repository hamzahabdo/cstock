// Copyright (c) 2022, burjalmaha.com and contributors
// For license information, please see license.txt
frappe.ui.form.on("RMS Stock Inventory", {
	setup: function (frm) {
		frm.fields_dict.items.grid.get_field("item_code").get_query =
			function () {
				return {
					filters: {
						is_stock_item: 1,
					},
				};
			};
	},
	refresh: function (frm) {
		if (frm.doc.creation) {
			frm.doc.items.forEach((el) => {
				fill_child_table_fields(frm, el.doctype, el.name);
			});
		}
		if (
			frm.doc.docstatus === 1 &&
			frm.doc.stock_item_supply_reference === undefined &&
			frm.doc.stock_item_release_reference === undefined
		) {
			frm.trigger("add_context_button");
		}
		if (frm.doc.docstatus === 0) {
			frm.trigger("add_get_items_button");
		}
	},
	add_context_button(frm) {
		frm.add_custom_button(__("Make Inventory"), () => {
			frappe.warn(
				"Confermation",
				"DO you want to continue the process?",
				() => {
					frappe.call({
						method: "custom_stock.custom_stock.doctype.rms_stock_inventory.rms_stock_inventory.get_stock_ledger_entries",
						args: {
							doc: frm.doc,
						},
						callback: (r) => {
							location.reload();
						},
					});
				},
				"Continue",
				false
			);
		});
	},
	add_get_items_button(frm) {
		let tmp_list = [];
		let data = [];
		let duplicate_elements = [];
		frm.add_custom_button(__("Get Items"), () => {
			frappe.call({
				method: "custom_stock.custom_stock.doctype.rms_stock_inventory.rms_stock_inventory.get_all_items",
				args: {
					warehouse: frm.doc.warehouse,
					posting_date: frm.doc.posting_date,
				},
				callback: (r) => {
					data = r.message;
					tmp_list = [...data];
					for (let i = 0; i < data.length; i++) {
						for (let y = 0; y < frm.doc.items.length; y++) {
							if (
								data[i].item_code === frm.doc.items[y].item_code
							) {
								duplicate_elements.push(i);
							}
						}
					}
					if (duplicate_elements.length > 0) {
						add_non_existent_items(
							frm,
							fillter_duplicate_items(
								tmp_list,
								duplicate_elements
							)
						);
					} else {
						add_non_existent_items(frm, tmp_list);
					}
				},
			});
		});
	},
});

frappe.ui.form.on("RMS Item Inventory", {
	item_code: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.item_code === undefined) {
			remove_child_table_data(frm, cdt, cdn);
		}
		if (row.item_code !== undefined) {
			fill_child_table_fields(frm, cdt, cdn);
		}
	},
	uom: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.qty !== undefined) {
			get_conversion(frm, cdn, cdt);
		}
	},
	qty: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.uom !== undefined) {
			get_conversion(frm, cdn, cdt);
		}
	},
});
function get_conversion(frm, cdn, cdt) {
	const row = locals[cdt][cdn];
	if (row.item_code !== undefined) {
		frappe.call({
			method: "custom_stock.custom_stock.doctype.rms_stock_inventory.rms_stock_inventory.get_conversion",
			args: {
				item_code: row.item_code,
				uom: row.uom,
			},
			callback: (r) => {
				const conversion_f = r.message;
				frappe.model.set_value(
					cdt,
					cdn,
					"conversion_factor",
					conversion_f[0].conversion_factor
				);
				frappe.model.set_value(
					cdt,
					cdn,
					"stock_qty",
					conversion_f[0].conversion_factor * row.qty
				);
			},
		});
	}
}
function fill_child_table_fields(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.call({
		method: "custom_stock.custom_stock.doctype.rms_stock_inventory.rms_stock_inventory.get_item_uom",
		args: {
			item_code: row.item_code,
		},
		callback: (r) => {
			const da = r.message;
			let tmp_list = [];
			let stock_uom = "";
			for (let i of da) {
				tmp_list.push(i.uom);
				if (i.conversion_factor === 1) {
					stock_uom = i.uom;
				}
			}
			frappe.meta.get_docfield("RMS Item Inventory", "uom", cdn).options =
				tmp_list;
			frappe.model.set_value(cdt, cdn, "stock_uom", stock_uom);
			// frappe.model.set_value(cdt, cdn, "conversion_factor", 1);
			refresh_child_table_fields(frm);
		},
	});
}

function add_non_existent_items(frm, items) {
	if (items.length > 0) {
		for (let i = 0; i < items.length; i++) {
			frm.add_child("items", {
				item_code: items[i].item_code,
				uom: items[i].stock_uom,
				stock_uom: items[i].stock_uom,
				item_name: items[i].item_name,
				qty: 0,
				conversion_factor: 1,
				stock_qty: 0,
			});
		}
		cur_frm.save();
	}
}
function fillter_duplicate_items(items, index_list) {
	let tmp_list = [];
	tmp_list = items;
	for (let i = index_list.length - 1; i >= 0; i--) {
		tmp_list.splice(index_list[i], 1);
	}
	return tmp_list;
}
function refresh_child_table_fields(frm) {
	frm.refresh_fields("uom");
	frm.refresh_fields("qty");
	frm.refresh_fields("conversion_factor");
	frm.refresh_fields("stock_qty");
}
function remove_child_table_data(frm, cdt, cdn) {
	frappe.meta.get_docfield("RMS Item Inventory", "uom", cdn).options = [];
	frappe.model.set_value(cdt, cdn, "uom", []);
	frappe.model.set_value(cdt, cdn, "qty", 0);
	frappe.model.set_value(cdt, cdn, "conversion_factor	", 0);
	frappe.model.set_value(cdt, cdn, "stock_qty	", 0);

	refresh_child_table_fields(frm);
}