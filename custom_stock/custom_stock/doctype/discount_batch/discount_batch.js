// Copyright (c) 2021, BM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Discount Batch', {
	refresh(frm) {
		const $grid_body = frm.$wrapper.find('[data-fieldname=items] ').find('.grid-body');
		$grid_body.addClass('grid-cart');
	},
	scan_barcode(frm) {
		if (frm.doc.scan_barcode) {
			frm.call({
				method: "get_item_row",
				args: { search_value: frm.doc.scan_barcode }
			}).then(r => {
				const data = r.message;
				if (!check_exist(data.item_code, frm.doc.items, null)) {
					let row = frm.add_child("items");
					row.item_code = data.item_code;
					row.item_name = data.item_name;
					row.new_price = frm.doc.default_new_price;
					frm.refresh_field("items");
				}
				frm.set_value("scan_barcode", "");
			});
		}
	}
});

frappe.ui.form.on('Discount Batch Item', {
	item_code(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!check_exist(row.item_code, frm.doc.items, row.name)) {
			row.new_price = frm.doc.default_new_price;
		} else {
			row.item_name = "";
			row.item_code = "";
		}
		frm.refresh_field("items");
	}
});

function check_exist(item_code, items, doc_name) {
	let exist = false;
	if (items) {
		items.forEach(i => {
			if (i.item_code == item_code && i.name != doc_name) {
				exist = true;
				return;
			}
		});
	}
	return exist;
}