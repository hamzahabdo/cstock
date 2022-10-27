// Copyright (c) 2020, BM and contributors
// For license information, please see license.txt
frappe.ui.form.on("Stock Inventory", {
  setup(frm) {
    frm.scan_barcode_trigger = true;
  },
  refresh(frm) {
    if (
      navigator.userAgent.match(/Android/i) ||
      navigator.userAgent.match(/webOS/i) ||
      navigator.userAgent.match(/iPhone/i) ||
      navigator.userAgent.match(/iPad/i) ||
      navigator.userAgent.match(/iPod/i) ||
      navigator.userAgent.match(/BlackBerry/i) ||
      navigator.userAgent.match(/Windows Phone/i)
    ) {
      barcodeScanning(frm);
    }
    frm.events.set_autosave_interval(frm);
    frm.events.prepare_frm(frm);
    frm.events.trigger_scan_barcode(frm);
  },
  prepare_frm(frm) {
    frm.doc.qty_count = 0;
    if (!frm.is_new()) {
      frm.get_field("scan_barcode").set_focus();
    }
    const $grid_body = frm.$wrapper.find("[data-fieldname=items] ").find(".grid-body");
    const $grid_body_last = frm.$wrapper.find("[data-fieldname=last_items] ").find(".grid-body");

    $grid_body.addClass("grid-cart");
    $grid_body_last.addClass("grid-cart");

    const scan_barcode_field = frm.fields_dict["scan_barcode"];
    scan_barcode_field.set_new_description("");
  },
  interval(frm) {
    frm.events.set_autosave_interval(frm);
  },
  set_autosave_interval(frm) {
    if (
      frm.doc.title &&
      frm.doc.warehouse &&
      frm.doc.items &&
      frm.doc.items[0].item_code != undefined &&
      frm.doc.interval > 0
    ) {
      const interval = frm.doc.interval * 60000;

      setTimeout(() => {
        frm.save();
      }, interval);
    }
  },
  set_autosave_counts(frm) {
    if (
      frm.doc.title &&
      frm.doc.warehouse &&
      frm.doc.items &&
      frm.doc.items[0].item_code != undefined &&
      frm.doc.items_count > 0
    ) {
      frm.doc.qty_count++;
      if (frm.doc.qty_count >= frm.doc.items_count) {
        frm.save();
      }
    }
  },
  scroll_to_item(frm, idx) {
    const $grid_body = frm.$wrapper.find("[data-fieldname=items]").find(".grid-body");
    const $item = $grid_body.find(`[data-idx="${escape(idx)}"]`);
    if ($item.length === 0) return;
    const scrollTop = $item.offset().top - $grid_body.offset().top + $grid_body.scrollTop();
    const $all = $grid_body.find(".cell-highlight");
    const $all_bg = $grid_body.find(".cell-highlight-bg");
    // const $qty = frm.$wrapper.find(`[data-idx="${escape(idx)}"]`).find(`[data-fieldname="qty"]`).find('.ellipsis');
    // $qty.addClass("scale-up");
    // console.log($qty);
    $all.removeClass("cell-highlight");
    $all_bg.removeClass("cell-highlight-bg");
    $item.addClass("cell-highlight");
    $item.addClass("cell-highlight-bg");
    setTimeout(() => $item.removeClass("cell-highlight"), 200);
    $grid_body.animate({ scrollTop });
  },
  // scan_barcode: function (frm) {
  // 	frm.events.scan_barcode_or_item_code(frm);
  // },
  trigger_scan_barcode(frm) {
    if (frm.scan_barcode_trigger) {
      frm.fields_dict["scan_barcode"].$input.on("keyup", (e) => {
        e.preventDefault();
        if (e.which === 13) {
          frm.events.scan_barcode_or_item_code(frm);
          e.stopPropagation();
        }
      });
      frm.scan_barcode_trigger = false;
    }
  },
  scan_barcode_or_item_code(frm) {
    let scan_barcode_field = frm.fields_dict["scan_barcode"];

    function show_description(item_code, idx, exist = null) {
      if (exist) {
        scan_barcode_field.set_new_description(
          __(`Row #${idx}: Item <b>${item_code}</b> Qty increased by ${frm.doc.punch_count || 1}`)
        );
      } else {
        scan_barcode_field.set_new_description(__(`Row #${idx}: Item <b>${item_code}</b> added`));
      }
    }

    if (frm.doc.scan_barcode) {
      frm
        .call({
          method: "search_serial_or_batch_or_barcode_number_or_item_code",
          args: { search_value: frm.doc.scan_barcode },
        })
        .then((r) => {
          const data = r && r.message;
          if (!data || Object.keys(data).length === 0) {
            scan_barcode_field.set_new_description(__("Cannot find this item!"));
            frappe.throw(__("Cannot find this item!"));
            return;
          }

          let cur_grid = frm.fields_dict.items.grid;

          let row_to_modify = null;
          const existing_item_row = frm.doc.items.find((d) => d.item_code === data.item_code);
          const blank_item_row = frm.doc.items.find((d) => !d.item_code);

          if (existing_item_row) {
            row_to_modify = existing_item_row;
          } else if (blank_item_row) {
            row_to_modify = blank_item_row;
          }

          if (!row_to_modify) {
            row_to_modify = frappe.model.add_child(frm.doc, cur_grid.doctype, "items");
          }

          show_description(data.item_code, row_to_modify.idx, row_to_modify.item_code);

          frm.from_barcode = true;
          frappe.model.set_value(row_to_modify.doctype, row_to_modify.name, {
            item_code: data.item_code,
            qty: (row_to_modify.qty || 0) + (frm.doc.punch_count || 1),
          });

          frm.events.set_autosave_counts(frm);

          scan_barcode_field.set_value("");
          frm.refresh_field("items");
          frm.events.set_last_items_iserted(frm, data);
          frm.events.scroll_to_item(frm, row_to_modify.idx);
        });
    }
    return false;
  },
  last_items_count(frm) {
    const count = frm.doc.last_items_count;
    const length = frm.doc.last_items.length;
    if (count < length && count != 0) {
      easy_pos.utils.splice_and_rearrange_grid(frm, "last_items", length - count);
      frm.refresh_field("last_items");
    }
  },
  set_last_items_iserted(frm, data) {
    if (frm.doc.last_items.length >= (frm.doc.last_items_count || 10)) {
      easy_pos.utils.splice_and_rearrange_grid(frm, "last_items");
    }

    let last_row_inserted = frm.doc.last_items.find((d) => !d.item_code);

    if (!last_row_inserted) {
      last_row_inserted = frm.add_child("last_items");
    }

    frappe.model.set_value(last_row_inserted.doctype, last_row_inserted.name, {
      item_code: data.item_code,
      qty: frm.doc.punch_count || 1,
    });
    frm.refresh_field("last_items");

    const $grid_body_last = cur_frm.$wrapper.find("[data-fieldname=last_items] ").find(".grid-body");
    const scrollTop = $grid_body_last.height();
    $grid_body_last.animate({ scrollTop });
  },
});

[
  { dt: "Stock Inventory Item", dn: "items" },
  { dt: "Stock Inventory Last Item", dn: "last_items" },
].forEach((doctype) => {
  easy_pos.utils.add_missing_values_based_on_trigger(doctype.dt, "item_code", (frm, d) => {
    frappe.db.get_doc("Item", d.item_code).then((r) => {
      d.item_name = r.item_name;
      d.item_group = r.item_group;
      frm.refresh_field(doctype.dn);
    });
  });
});

var codeReader = null;
function barcodeScanning(frm) {
  let barcodeContainer = document.querySelector(".custom_barcode_container");
  barcodeContainer.style.display = "block";
  let selectedDeviceId;
  // initilize barcode scanner
  codeReader = new ZXing.BrowserBarcodeReader();
  console.log("code reader initialized");
  // get user media (the list of cameras in the device) and show it in select element and add listener to it
  //  add listener to buttons
  document.getElementById("startButton").addEventListener("click", () => {
    codeReader
      .getVideoInputDevices()
      .then((videoInputDevices) => {
        const sourceSelect = document.getElementById("sourceSelect");
        let selectedDeviceId = videoInputDevices[0].deviceId;
        if (sourceSelect.childElementCount == 0) {
          if (videoInputDevices.length > 1) {
            selectedDeviceId = videoInputDevices[1].deviceId;
            videoInputDevices.forEach((element) => {
              const sourceOption = document.createElement("option");
              sourceOption.text = element.label;
              sourceOption.value = element.deviceId;
              sourceSelect.appendChild(sourceOption);
            });

            sourceSelect.onchange = () => {
              selectedDeviceId = sourceSelect.value;
            };

            const sourceSelectPanel = document.getElementById("sourceSelectPanel");
            sourceSelectPanel.style.display = "block";
          }
        }
        decodeBarcode(frm, selectedDeviceId);
      })
      // catch if there is an error in  getting device media
      .catch((err) => {
        frappe.msgprint({ title: "User Media Error", indicator: "red", message: err.message });
      });
  });

  document.getElementById("resetButton").addEventListener("click", () => {
    codeReader.reset();
  });
}
function decodeBarcode(frm, deviceID) {
  codeReader
    .decodeOnceFromVideoDevice(deviceID, "video")
    .then((result) => {
      console.log(result);
      frm.set_value("scan_barcode", result.text);
      decodeBarcode(frm, deviceID);
    })
    .catch((err) => {
      frappe.msgprint({ title: "Error", indicator: "red", message: err.message });
    });
}
