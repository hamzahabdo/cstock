// Copyright (c) 2020, BM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pricing', {

});

frappe.ui.form.on('Pricing List', {
	price_lists_add: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		row.ratio = frm.doc.ratio;
		row.minimum__rate = frm.doc.value;
		frm.refresh_field('price_lists');
	}
});

cur_frm.cscript.get_items = function (doc) {
	cur_frm.clear_table("priced_items");
	cur_frm.clear_table("items");
	cur_frm.call('get_prices', {
		'source_name': getSource(),
		'source_type': doc.get_from,
		'price_lists': doc.price_lists,
		'is_ratio': doc.is_ratio,
		'min_rate_is_ratio': doc.min_rate_is_ratio
	})
		.then(r => {
			cur_frm.set_df_property('items', 'hidden', '0');
			cur_frm.set_df_property('priced_items', 'hidden', '0');
			for (let i of r.message) {
				if (i.priced) {
					cur_frm.add_child('priced_items', {
						'item': i.item,
						'item_name': i.item_name,
						'price_list': i.price_list,
						'rate': i.rate,
						'minimum_rate': i.minimum_rate,
						'valuation': i.valuation,
						'profit': (i.rate - i.valuation) / i.valuation * 100,
						'item_price': i.item_price
					});
					cur_frm.refresh_field('priced_items');
				} else {
					cur_frm.add_child('items', {
						'item': i.item,
						'item_name': i.item_name,
						'price_list': i.price_list,
						'rate': i.rate,
						'minimum_rate': i.minimum_rate,
						'valuation': i.valuation,
						'profit': (i.rate - i.valuation) / i.valuation * 100
					});
					cur_frm.refresh_field('items');
				}
			}
		})
}

function getSource() {
	if(cur_frm.doc.get_from == 'Purchase Invoice') {
		return cur_frm.doc.purchase_invoice;
	} else if (cur_frm.doc.get_from == 'Stock Entry') {
		return cur_frm.doc.stock_transfer;
	} else if (cur_frm.doc.get_from == 'Purchase Receipt') {
		return cur_frm.doc.purchase_receipt;
	} else if (cur_frm.doc.get_from == 'Discount Batch') {
		return cur_frm.doc.discount_batch;
	}
}
