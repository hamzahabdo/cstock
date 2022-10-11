// Copyright (c) 2021, BM and contributors
// For license information, please see license.txt

frappe.ui.form.on('Custom Label Printing', {
	label_text(frm) {
		frm.refresh();
	},
	copies(frm) {
		frm.refresh();
	},
	refresh: function (frm) {
		if (!frm.doc.label_text) {
			frm.get_field('label_text').set_focus();
		}
		frm.events.set_custom_buttons(frm);
		frm.page.clear_primary_action();
		frm.page.clear_indicator();
	},
	set_custom_buttons(frm) {
		if (frm.doc.label_text && frm.doc.copies) {
			frm.add_custom_button(__("Print Lable"), () => {
				frm.events.print_label(frm);
			});
		}
	},
	validate() {
		frappe.throw(__("You can't save this document!"));
	},
	print_label(frm) {
		const $label_markup = frm.events.generate_markup(frm);
		const options = {
			copies: frm.doc.copies,
		};

		frappe.ui.form.qz_connect()
			.then(() => {
				qz.printers.getDefault().then((printer) => {
					const config = qz.configs.create(printer, options);
					const data = [{
						type: 'html',
						format: 'plain',
						data: $label_markup
					}];
					return qz.print(config, data);
				});
			})
			.then(frappe.ui.form.qz_success)
			.catch(err => {
				frappe.ui.form.qz_fail(err);
			});

	},
	generate_markup(frm) {
		return `
		<div id="markup">
			<center>
				<p>${frm.doc.label_text}</p>
			</center>
		</div>
		`;
	}
});
