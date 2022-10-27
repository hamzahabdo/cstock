// Copyright (c) 2020, BM and contributors
// For license information, please see license.txt

frappe.ui.form.on("Items Barcode Printing", {
  branch(frm) {
    frm.set_value("price_list", "");
  },
  price_list(frm) {
    frm.set_value("print_from", __("Manual Entry"));
  },
  print_from(frm) {
    frm.set_value("document_no", "").then(() => {
      if (frm.doc.print_from != __("Manual Entry")) {
        //to be reviewd
        empty_table(frm);
        change_grid_status(frm);
        frm.get_field("document_no").set_focus();

        frm.set_query("document_no", function (doc) {
          return {
            filters: {
              branch: doc.branch,
            },
          };
        });
      } else {
        frm.grids[0].$wrapper.find(".grid-row-check").prop("checked", false);
        empty_table(frm);
        change_grid_status(frm, "items", false, true, false);

        add_empty_row(frm);
      }
    });
  },
  document_no(frm) {
    empty_table(frm);

    if (frm.doc.document_no) {
      get_items(frm);
    }
  },
  printer_model(frm) {
    frm.refresh();
  },
  printer_name(frm) {
    frm.refresh();
  },
  validate(frm) {
    frappe.throw(__("You can't save this document!"));
  },
  print_barcode(frm, model) {
    const items_all = frm.doc.items;

    let items = [],
      items_s = [];
    if (frm.doc.print_from == __("Manual Entry")) {
      items = items_all;
    } else {
      items_s = frm.get_selected();

      if (items_s) {
        for (let i = 0; i < items_all.length; i++) {
          const element = items_all[i];
          for (let j = 0; j < items_s.items.length; j++) {
            const element_s = items_s.items[j];
            if (element.name == element_s) {
              items.push(element);
            }
          }
        }
      }
    }

    let items_to_print = [];

    for (let i of items) {
      if (i.item) {
        if (!i.barcode) {
          i.barcode = i.item;
        }
        items_to_print.push(i);
      } else {
        popup_msg("There are no items to print", "No Items", "orange");
      }
    }

    if (items_to_print[0]) {
      print_barcode(frm, items_to_print, frm.doc.layout, model);
    }
  },
  set_custom_buttons(frm) {
    let model = frm.doc.printer_model || "ZDesigner",
      layouts = get_printer_layouts(model);
    frm.doc.layout = layouts[0];
    frm.page.add_inner_message(frm.doc.layout);
    for (const layout of layouts) {
      frm.page.add_inner_button(
        layout,
        () => {
          frm.doc.layout = layout;
          frm.page.add_inner_message(frm.doc.layout);
        },
        __("Print Layout")
      );
    }
    // frm.page.add_inner_button(small,
    // 	() => {
    // 		frm.doc.layout = small;
    // 		frm.page.add_inner_message(frm.doc.layout);
    // 	}, __('Print Layout'));
    if (frm.doc.printer_model && frm.doc.printer_name) {
      frm.add_custom_button(__("Print Barcode"), () => {
        frm.events.print_barcode(frm, model);
      });
    }
  },
  onload(frm) {
    add_empty_row(frm);
    // frm.set_value('printer_name', 'barcode');
  },
  refresh(frm) {
    // frm.refresh();
    frm.events.set_custom_buttons(frm);
    // frm.page.set_primary_action(__('Print Barcode'),
    // 	function () {

    // 	}, 'fa fa-print');
    frm.page.clear_primary_action();
    frm.page.clear_indicator();
    // add_empty_row(frm);
    // frm.grids[0].check_all_rows();
    // frm.set_value("branch", "إن سيتي سكاكا").then(() => {

    // 	frm.set_value("price_list", "ان سيتي سكاكا").then(() => {
    // 		// frm.set_value("printer_model", "ZDesigner").then(() => {
    // 		// 	frm.set_value("printer_name", "barcode").then(() => {
    // 		// 		// frm.events.print_barcode(frm);
    // 		// 	});
    // 		// });
    // 	});
    // });
    // frm.add_child("items", {
    // 	item: "4086",
    // 	item_name: "جلابيه نسائي ",
    // 	item_price: 200,
    // 	barcode: 123,
    // 	quantity: 1
    // });
    // frm.refresh_field("items");
    // console.log(get_markup());
    // print();
  },
});

frappe.ui.form.on("Items To Print", {
  msg: true,
  item(frm, cdt, cdn) {
    const item_row = locals[cdt][cdn];

    get_item(frm, item_row);
  },
  quantity(frm, cdt, cdn) {
    const item_row = locals[cdt][cdn];

    if (item_row.item != null) {
      if (item_row.quantity == null) {
        no_item_msg(frm, item_row);
      }
    } else {
      no_item_msg(frm, item_row);
    }
  },
});

var msg = true;

function get_item(frm, item_row) {
  if (item_row.item != null) {
    frm.call({
      method: "get_single_item",
      args: {
        item_code: item_row.item,
        branch: frm.doc.branch,
        price_list: frm.doc.price_list,
      },
      callback: function (r) {
        if (r.message) {
          let i = r.message;
          if (i.item_price != "") {
            console.log(i.item_price);
            if (i.quantity != null) {
              item_row.barcode = i.barcode;
              item_row.item_price = i.item_price;
              item_row.quantity = i.quantity;
              item_row.previous_price = i.previous_price;
              item_row.percentage_change = i.percentage_change;
            } else {
              popup_msg(
                `Item ${item_row.item_name} does not have enough quantity in the stock`,
                `Item Code: ${item_row.item}`,
                "red"
              );

              msg = !msg;

              clear_cur_row(frm, item_row);
            }
          } else {
            popup_msg(
              `Item ${item_row.item_name} is not included in the specified price list`,
              `Item Code: ${item_row.item}`,
              "red"
            );

            msg = !msg;
            clear_cur_row(frm, item_row);
          }

          frm.refresh_field("items");
        }
      },
    });
  } else {
    if (msg) {
      no_item_msg(frm, item_row);
    }
    msg = true;
  }
}

function popup_msg(message, title, indicator_color) {
  frappe.msgprint({
    indicator: indicator_color,
    title: __(title),
    message: __(message),
  });
}

function no_item_msg(frm, item_row) {
  clear_cur_row(frm, item_row);
  popup_msg("Please insert the item code first", "Missing Item Code", "orange");
}

function clear_cur_row(frm, item_row) {
  item_row.item = null;
  item_row.item_name = "";
  item_row.barcode = "";
  item_row.item_price = "";
  item_row.quantity = "";
  frm.refresh_field("items");
}

function get_items(frm) {
  frm.call({
    method: "get_all_items",
    args: {
      source_type: frm.doc.print_from,
      source_name: frm.doc.document_no,
      price_list: frm.doc.price_list,
      branch: frm.doc.branch,
    },
    callback: function (r) {
      if (r.message) {
        for (let i of r.message) {
          if (i.item_price != "") {
            frm.add_child("items", {
              item: i.item,
              item_name: i.item_name,
              item_price: i.item_price,
              previous_price: i.previous_price,
              percentage_change: i.percentage_change,
              barcode: i.barcode,
              quantity: i.quantity,
            });
          }
        }
        frm.refresh_field("items");
        if (!frm.grids[0].$wrapper.find(".grid-row-check").prop("checked")) {
          frm.grids[0].check_all_rows();
        }
      }
    },
  });
}

function change_grid_status(
  context,
  table = "items",
  static_rows = true,
  sortable = false,
  read_only = true,
  field_index = 0
) {
  context.get_field(table).grid.sortable_status = sortable;
  context.get_field(table).grid.docfields[field_index].read_only = read_only;
  context.refresh_field(table);
}

function add_empty_row(context) {
  context.add_child("items");
  context.refresh_field("items");
}

function empty_table(context) {
  context.clear_table("items");
  context.refresh_field("items");
}

function make_dom() {
  $(".layout-main-section").append(
    `<div class="bc-container">
		 </div>`
  );
}

function print_barcode(context, items, layout, model) {
  let printer_name = context.doc.printer_name;
  if (!printer_name) {
    frappe.throw(__("Please, Select a printer first!"));
  }
  let markup_layout = get_markup_layout(model, layout);
  let printer_details = markup_layout[0];

  let width, height, container;

  width = printer_details.printer_width;
  height = printer_details.printer_height;

  let top = 0,
    right = 0,
    bottom = 0,
    left = 0;

  var data = [],
    options = [];

  for (const item of items) {
    make_dom();
    container = $(".bc-container");
    container.append(generate_markup(item, markup_layout));

    data.push({
      type: "html",
      format: "plain",
      data: $("#markup").html(),
    });

    options.push({
      copies: item.quantity,
      size: { width: width, height: height },
      units: "in",
      margins: [top, right, bottom, left],
      density: "1000",
      interpolation: "nearest-neighbor",
      rasterize: "false",
    });
    container.remove();

    if (items.length == 1) break;

    if (context.doc.print_with_break) {
      data.push({
        type: "html",
        format: "plain",
        data: "<div style='font-size: 40pt; font-weight: bolder; text-align: center'>فـــــاصل</div>",
      });

      options.push({
        copies: 1,
        size: { width: width, height: height },
        units: "in",
        margins: [top, right, bottom, left],
        density: "1000",
        interpolation: "nearest-neighbor",
        rasterize: "false",
      });
    }
  }

  var chain = [];

  for (var i = 0; i < data.length; i++) {
    (function (i_) {
      //setup this chain link
      var link = function () {
        return qz.printers.find(printer_name).then(function (found) {
          return qz.print(qz.configs.create(found, options[i_]), [data[i_]]);
        });
      };

      chain.push(link);
    })(i);
    //closure ensures this promise's concept of `i` doesn't change
  }

  var firstLink = frappe.ui.form.qz_connect();

  var lastLink = null;
  chain.reduce(function (sequence, link) {
    lastLink = sequence.then(link);
    context.page.set_indicator("Printing Now ...", "orange");
    return lastLink;
  }, firstLink);

  //this will be the very last link in the chain
  lastLink.catch(function (err) {
    console.error(err);
  });
  lastLink.finally(function () {
    context.page.set_indicator("Finished Printing :)", "green");
  });
}

function get_printer_layouts(printer) {
  let layouts;
  frappe.call({
    method: "custom_stock.custom_stock.doctype.items_barcode_printing.items_barcode_printing.get_printer_layouts",
    args: {
      printer: printer,
    },
    async: false,
    callback: (r) => {
      layouts = r.message;
    },
  });
  return layouts;
}

function get_markup_layout(model, layout) {
  let print_details;
  frappe.call({
    method: "custom_stock.custom_stock.doctype.items_barcode_printing.items_barcode_printing.get_markup_layout",
    args: {
      model: model,
      layout: layout,
    },
    async: false,
    callback: (r) => {
      print_details = r.message;
    },
  });
  return print_details;
}

function generate_markup(item, markup_layout) {
  let markup;
  let dim = [],
    details = [],
    par = [];

  dim.push(markup_layout[0].html_width);
  dim.push(markup_layout[0].html_height);

  for (const par of markup_layout[1].parameters) {
    details.push(item[par.parameter_name]);
  }
  par = dim.concat(details);
  markup = markup_layout[1].markup.indexFormat(par);

  return markup;
}
