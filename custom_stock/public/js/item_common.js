// frappe.ui.form.on('Item', {
//     before_save: function (frm) {
//         let row = frm.add_child('supplier_items', {
//             supplier: frm.doc.n_supplier,
//             supplier_part_no: frm.doc.item_code
//         });
//     }
// });

frappe.ui.form.on("Item", {
  // n_supplier(frm) {
  //     set_barcode(frm);
  // },
  validate(frm) {
    // set_barcode(frm);
    check_barcode_length(frm);
  },
  // ,
  // item_group(frm) {
  //     frm.clear_table("item_dimensions");
  //     frappe.db.get_doc('Item Group', frm.doc.item_group).then((r) => {
  //         var d_list = r.item_dimensions;
  //         for (let d of d_list) {
  //             frm.add_child('item_dimensions',
  //                 {
  //                     item_dimension: d.item_dimension,
  //                     item_dimension_type: d.item_dimension_type
  //                 }
  //             )
  //             frm.refresh_field("item_dimensions");
  //         }
  //     })
  // }
});

function set_barcode(frm) {
  frappe.call({
    method: "nct.common.barcode_generator.get_last_barcode",
    callback: (r) => {
      if (r.message) {
        let barcode = r.message;

        barcode++;

        barcode = String(barcode).padStart(10, "0");

        if (frm.doc.barcodes != undefined) {
          if (frm.doc.barcodes.length > 0) {
            if (frm.doc.barcodes[0].barcode == undefined || frm.doc.barcodes[0].barcode == "") {
              frm.doc.barcodes[0].barcode = barcode;
            } else {
              if (frm.doc.barcodes[0].parent != frm.doc.item_code) {
                frm.doc.barcodes[0].barcode = barcode;
              }
            }
          }
        } else {
          frm.add_child("barcodes", {
            barcode: barcode,
          });
        }

        frm.refresh_field("barcodes");
      } else {
        frappe.throw(__("Something went wrong"));
      }
    },
  });
}
function check_barcode_length(frm) {
  if (frm.doc.barcodes !== undefined) {
    if (frm.doc.barcodes[0].barcode !== undefined) {
      for (var i of frm.doc.barcodes) {
        if (i.barcode.length > 10 || contains_anyLetters(i.barcode)) {
          frappe.throw("barcode length shoud be less than or equal 10 and content only numbers");
        }
      }
    }
  }
}

function contains_anyLetters(barcode) {
  return /[a-zA-Z]/.test(barcode);
}
