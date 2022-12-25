frappe.ui.form.on("Stock Entry Detail", {
  qty(frm, cdt, cdn) {
    getTotalOfQty(frm, cdt);
  },
  items_remove(frm, cdt, cdn) {
    getTotalOfQty(frm, cdt);
  },
});
frappe.ui.form.on("Stock Entry", {
  onload(frm) {
    if (frm.doc.docstatus < 1) {
      frm.set_value("expense_account", "");
    }
    // frappe.call("custom_stock.common.stock_common.override_scan_barcode");
  },
  //TODO Check warehouse filter
  refresh(frm) {
    frm.set_query("item_code", "items", function () {
      if (frm.doc.stock_entry_type == "Send to Warehouse") {
        return {
          query: "custom_stock.common.stock_common.get_available_items",
          filters: {
            warehouse: frm.doc.from_warehouse,
          },
        };
      }
    });

    //Old System migration
    // if (frm.doc.docstatus == 0) {
    //     frm.add_custom_button(__("Prepare Entry"), () => {
    //         frm.events.show_query_dialog(frm);
    //     });
    //     frm.set_value('set_posting_time', 1);
    // }
    /////////////////////////////////////////////////////////////////
    // setTimeout((r)=>{
    //     frm.toggle_display("naming_series", false);
    // }, 150);
    frm.set_df_property("naming_series", "read_only", true);
    // frm.get_field("naming_series").toggle(false);
  },
  update_target_quantities(frm) {
    frm.doc.items.forEach((i) => {
      let d = locals[i.doctype][i.name];
      if (d.item_code && frm.doc.target_warehouse) {
        frappe.call({
          method: "custom_stock.common.stock_common.get_qty_at_warehouse",
          args: {
            item_code: d.item_code,
            warehouse: frm.doc.target_warehouse,
          },
          callback: (r) => {
            d.qty_at_target = r.message;
          },
        });
      }
    });
    frm.script_manager.trigger("from_warehouse");
  },
  show_query_dialog(frm) {
    const me = this;
    return new Promise((resolve) => {
      let prepare_entry = (se) => {
        frm.events.get_query(frm, se.bill_no, se.o_warehouse, se.d_warehouse);
      };

      var dialog = frappe.prompt(
        [
          {
            fieldtype: "Int",
            label: __("Entry Refrence"),
            fieldname: "bill_no",
            reqd: 1,
          },
          {
            fieldtype: "Section Break",
          },
          {
            fieldtype: "Int",
            label: __("Source Warehouse"),
            fieldname: "o_warehouse",
            reqd: 1,
          },
          {
            fieldtype: "Column Break",
          },
          {
            fieldtype: "Int",
            label: __("Target Warehouse"),
            fieldname: "d_warehouse",
            reqd: 1,
          },
        ],
        prepare_entry,
        __("Stock Entry Information"),
        __("Get Entry Details")
      );
    });
  },
  get_query(frm, bill_no, o_warehouse, d_warehouse) {
    var method = "nct.common.oracle_connection.get_stock_entry_details",
      args = {
        bill_no: bill_no,
        source_warehouse: o_warehouse,
        target_warehouse: d_warehouse,
      };

    frm.clear_table("items");

    frappe.call({
      method: method,
      args: args,
      async: false,
      callback: (r) => {
        if (r && r.message) {
          var items = r.message;

          // console.log(info);
          for (const key in items) {
            if (items.hasOwnProperty(key)) {
              const item = items[key];
              frm.add_child("items", {
                item_code: item.item_code,
                item_name: item.item_name,
                description: item.item_name,
                uom: "حبه",
                qty: item.qty,
                conversion_factor: 1,
                stock_uom: "حبه",
                transfer_qty: item.qty,
                expense_account: "51010107 - تسوية المخزون - NCT",
              });
            }
          }
          frm.refresh_field("items");

          frm.set_value("stock_entry_type", "Send to Warehouse").then(() => {
            let msg = __("Stock Entry is ready to be saved and submitted!");

            frappe.msgprint(msg);
          });
        } else {
          frappe.msgprint(__("Operation did not succeed! please try again!"));
        }
      },
    });
  },
  remarks_area(frm) {
    easy_pos.utils.copy_new_to_old(frm, "remarks_area", "remarks");
  },
  stock_entry_type(frm) {
    if (
      frm.doc.stock_entry_type == "Material Issue" ||
      frm.doc.stock_entry_type == "Material Receipt" ||
      frm.doc.stock_entry_type == "أمر صرف مخزني" ||
      frm.doc.stock_entry_type == "أمر توريد مخزني"
    ) {
      frm.doc.tw = frm.doc.sw;
    }
  },
});

function getTotalOfQty(frm, cdt) {
  let d = locals[cdt];
  let total = 0;
  Object.keys(d).forEach((key) => {
    if (!isNaN(d[key].qty)) {
      total += d[key].qty;
    }
  });

  frm.set_value("qty_total", total);
}
