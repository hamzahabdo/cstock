frappe.ui.form.on('Stock Entry Detail', {
    item_code(frm, cdt, cdn) {
        let d = locals[cdt][cdn];

        if (d.item_code && frm.doc.target_warehouse) {
            if (frm.doc.from_warehouse && frm.doc.to_warehouse) {
                d.s_warehouse = frm.doc.from_warehouse;
                d.t_warehouse = frm.doc.to_warehouse;
            }

            frappe.call({
                method: "custom_stock.common.stock_common.get_qty_at_warehouse",
                args: {
                    item_code: d.item_code,
                    warehouse: frm.doc.target_warehouse
                },
                callback: (r) => {

                    d.qty_at_target = r.message;
                }
            });
        }
    }
})