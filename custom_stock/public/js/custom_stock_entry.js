frappe.ui.form.on("Stock Entry", {
  refresh(frm) {
    frm.events.add_context_buttons(frm);
  },
  from_warehouse(frm) {
    frm.events.add_context_buttons(frm);
  },
  get_item_scrap(frm) {
    frappe.call({
      method: "custom_stock.common.custom_stock_entry.GetItemScrap",
      args: {
        warehouse: frm.doc.from_warehouse,
      },
      callback: (r) => {
        if (r && r.message) {
          frm.clear_table("items");
          frm.refresh_field("items");
          const scrap_item = r.message;
          for (var i in scrap_item) {
            let child = frm.add_child("items", {
              item_code: scrap_item[i]["item_code"],
              qty: scrap_item[i]["qty"],
              uom: scrap_item[i]["UOM"],
              stock_uom: scrap_item[i]["UOM"],
              conversion_factor: scrap_item[i]["conversion_factor"],
            });
            frm.refresh_field("items");
            frm.script_manager.trigger("qty", child.doctype, child.name);
          }
        }
      },
    });
  },
  add_context_buttons(frm) {
    if (frm.doc.from_warehouse && frm.doc.stock_entry_type)
      frm.add_custom_button(__("fetch Scrap"), () => {
        if (frm.doc.from_warehouse && frm.doc.stock_entry_type) {
          frm.events.get_item_scrap(frm);
        } else {
          frappe.throw("You have to select the Stock Entry Type and Default Source Warehouse");
        }
      });
  },
});
