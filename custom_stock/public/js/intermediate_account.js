var nct_settings;
frappe.ui.form.on('Stock Entry', {
    onload(frm) {
        // frm.events.set_basic_rate_read_only(frm);
        frm.toggle_enable('branch', false);
        // frappe.call({
        //     method: 'custom_stock.common.get_doc.get_single_doc',
        //     args: {
        //         doctype: 'Warehouse'
        //     },
        //     callback: (r) => {
        //         if (r.message) {
        //             nct_settings = r.message;
        //         }
        //     }
        // });
        toggle_fields(frm, false, 'to_warehouse', 'source_warehouse',
            'target_warehouse_address', 'source_warehouse_address');

        if (frm.doc.purpose == "Material Transfer") {
            if (frm.doc.outgoing_stock_entry) {
                frm.events.prepare_RAW(frm);
                receive_at_warehouse(frm);
            }
        }
    },
    refresh(frm) {
        frm.events.show_inventory_botton(frm);
        // if (frm.doc.purpose == "Material Transfer") {
        //     if (frm.doc.outgoing_stock_entry) {
        //         frm.events.prepare_RAW(frm);
        //         receive_at_warehouse(frm);
        //     }
        // }
    },
    purpose(frm) {
        frm.events.set_naming_series(frm);
        // frm.events.set_basic_rate_read_only(frm);
        frm.events.show_inventory_botton(frm);

        if (frm.doc.purpose == "Material Transfer") {
            if (frm.doc.outgoing_stock_entry) {
                frm.events.prepare_RAW(frm);
            } else{
                toggle_fields(cur_frm, false, 'source_warehouse', 'target_warehouse')
                toggle_fields(frm, true, 'to_warehouse');
            }
        }
        // else if (frm.doc.purpose == "Material Transfer") {
        //     if (frm.doc.outgoing_stock_entry) {
        //         frm.events.prepare_RAW(frm);
        //     }
        // }
        else if (frm.doc.purpose == "Material Issue") {
            frm.events.prepare_MI(frm);
        }
        else if (frm.doc.purpose == "Material Receipt") {
            frm.events.prepare_MR(frm);
        }
        else {
            reset_fields(frm, "", "from_warehouse", "to_warehouse", "branch");
        }
    },
    stock_entry_type(frm) {
        if (!frm.doc.stock_entry_type) {
            frm.set_value("purpose", "");
        }
        if (frm.doc.stock_entry_type != "Send to Warehouse") {
            frm.set_value("sw", "")
            frm.set_value("tw", "")
        } else {
            frm.set_value("tw", "")
        }
    },
    add_to_transit(frm){
        if(frm.doc.add_to_transit){
            frm.events.prepare_MT(frm);
        }else{
            toggle_fields(cur_frm, false, 'source_warehouse', 'target_warehouse')
            toggle_fields(frm, true, 'to_warehouse');
        }
    }
    ,
    show_inventory_botton(frm) {
        if (frm.doc.purpose == "Material Issue") {
            frm.events.get_inventory_items(frm, -1);
        }
        else if (frm.doc.purpose == "Material Receipt") {
            frm.events.get_inventory_items(frm, 1);
        }
        else {
            frm.events.get_inventory_items(frm, 0);
        }
    },
    get_inventory_items(frm, qty_type) {
        let qtys, _qtys, warehouse, btn_name = 'Get Items From Stock Inventory';

        if (qty_type === -1) {
            qtys = __('NEGATIVE')
            _qtys = __('POSITIVE')
            warehouse = 'from_warehouse';
        } else if (qty_type === 1) {
            qtys = __('POSITIVE')
            _qtys = __('NEGATIVE')
            warehouse = 'to_warehouse';
        }

        frm.remove_custom_button(__(btn_name));
        if (qty_type === 0) {
            return;
        }
        if (frm.doc.docstatus < 1) {
            frm.add_custom_button(__(btn_name), function () {
                nct.utils.empty_table(frm, 'items');
                erpnext.utils.map_current_doc({
                    method: "nct.ncity.doctype.stock_inventory.stock_inventory.make_stock_entry",
                    source_doctype: "Stock Inventory Processing",
                    target: frm,
                    date_field: "creation",
                    setters: {
                        // warehouse: undefined,
                    },
                    get_query_filters: {
                        docstatus: 1,
                        warehouse: frm.doc[warehouse]
                    }
                })
            });
        }
    },
    set_naming_series(frm) {
        var pattern;
        if (frm.doc.purpose == "Material Issue" || frm.doc.purpose == "Material Receipt") {
            pattern = "se_t.-.bn.MM.YY.-.#";
        }
        else {
            pattern = "se_t.-.sw.-.tw.-.MM.YY.-.#";
        }
        frm.set_value("naming_series", pattern);
    },
    outgoing_stock_entry(frm) {
        receive_at_warehouse(frm);
    },
    from_warehouse(frm) {
        frm.set_value("source_warehouse", frm.doc.from_warehouse).then(() => {
            frm.events.set_warehouse_acronym(frm, frm.doc.from_warehouse, "sw");
            if (!frm.doc.outgoing_stock_entry && frm.doc.add_to_transit) {
                frm.events.set_in_transit_warehouse(frm, frm.doc.from_warehouse);
            }
            // let to_ware = frm.doc.from_warehouse 
            // console.log(to_ware)
        });
        // if (frm.doc.purpose != "Receive at Warehouse") {
        //     set_branch(frm, frm.doc.from_warehouse);
        // }
        if (!frm.doc.outgoing_stock_entry) {
            set_branch(frm, frm.doc.from_warehouse);
        }
        // if (frm.doc.stock_entry_type == "أمر صرف مخزني") {
        //     frm.events.set_warehouse_acronym(frm, frm.doc.from_warehouse, "sw");
        //     frm.events.set_warehouse_acronym(frm, frm.doc.from_warehouse, "tw");
        // }
        if (frm.doc.purpose == __("Material Issue")) {
            frm.events.set_warehouse_acronym(frm, frm.doc.from_warehouse, "sw");
            frm.events.set_warehouse_acronym(frm, frm.doc.from_warehouse, "tw");
        }
    },
    to_warehouse(frm) {
        if (frm.doc.purpose == __("Material Receipt")) {
            frm.set_value("target_warehouse", frm.doc.to_warehouse).then(
                frm.events.set_warehouse_acronym(frm, frm.doc.to_warehouse, "sw")
            )
            set_branch(frm, frm.doc.to_warehouse);
        }
        if(frm.doc.purpose == __("Material Transfer") && !frm.doc.add_to_transit){
            frm.events.set_warehouse_acronym(frm, frm.doc.to_warehouse, "tw")
        }
        // if (frm.doc.stock_entry_type == "أمر توريد مخزني") {
        //     frm.set_value("target_warehouse", frm.doc.to_warehouse).then(
        //         frm.events.set_warehouse_acronym(frm, frm.doc.to_warehouse, "sw")
        //     )
        //     set_branch(frm, frm.doc.to_warehouse);
        // }
    },
    prepare_MT(frm) {
        toggle_fields(frm, false, 'to_warehouse', 'source_warehouse');
        toggle_fields(frm, true, 'from_warehouse', 'target_warehouse');
        reset_fields(frm, "", "target_warehouse");
        frm.set_df_property('target_warehouse', 'read_only', 0);


        // frm.set_value("from_warehouse", nct_settings.default_source_warehouse);
        // // frm.set_value("source_warehouse", nct_settings.default_source_warehouse);
        // frm.set_value("to_warehouse", nct_settings.intermediate_warehouse);

    },
    prepare_RAW(frm) {
        toggle_fields(frm, true, 'source_warehouse', 'target_warehouse');
        toggle_fields(frm, false, 'from_warehouse', 'to_warehouse');
        reset_fields(frm, "", "from_warehouse", "to_warehouse",
            "source_warehouse", "target_warehouse");
    },
    prepare_MI(frm) {
        toggle_fields(frm, false, 'source_warehouse', 'target_warehouse', 'to_warehouse');
        toggle_fields(frm, true, 'from_warehouse');
        reset_fields(frm, "", "from_warehouse", "to_warehouse",
            "source_warehouse", "target_warehouse", "branch");

    },
    prepare_MR(frm) {
        toggle_fields(frm, false, 'source_warehouse', 'from_warehouse', 'target_warehouse');
        toggle_fields(frm, true, 'to_warehouse');
        reset_fields(frm, "", "from_warehouse", "to_warehouse",
            "source_warehouse", "target_warehouse", "branch");

    },
    set_basic_rate_read_only(frm) {
        if (frm.doc.purpose == "Material Issue"
            || frm.doc.purpose == "Material Receipt") {
            frm.set_df_property("basic_rate", "read_only", 0, frm.doc.name, "items");
        }
        else {
            frm.set_df_property("basic_rate", "read_only", 1, frm.doc.name, "Items");
        }
    },
    set_warehouse_acronym(frm, warehouse, short_name) {
        var warehouse_acronym = "";
        frappe.call({
            method: "custom_stock.common.stock_common.get_warehouse_acronym",
            args: { "wname": warehouse }
        })
            .then(r => {
                if (r) {
                    warehouse_acronym = r.message;
                    frm.set_value(short_name, warehouse_acronym);
                }
            });
    },
    set_in_transit_warehouse(frm, warehouse) {
        var in_transit_warehouse = "";
        frappe.call({
            method: "custom_stock.common.stock_common.get_in_transit_warehous",
            args: { "wname": warehouse }
        })
            .then(r => {
                if (r) {
                    let message = r.message;
                    console.log(message);
                    in_transit_warehouse = message;
                    frm.set_value("to_warehouse", in_transit_warehouse);
                }
            });

    },
    test_set_warehouse_acronym(frm, warehouse, short_name) {
        // if (warehouse) {
        var warehouse_acronym = "";
        var intermediate_warehouse = "";
        frappe.call({
            method: "custom_stock.common.stock_common.get_warehouse_acronym",
            args: { "wname": warehouse }
        })
            .then(r => {
                if (r) {
                    let message = r.message;
                    console.log(message);
                    warehouse_acronym = message.short_name;
                    frm.set_value(short_name, warehouse_acronym);
                    intermediate_warehouse = message.transit_warehouse
                    if (!frm.doc.outgoing_stock_entry) {
                        frm.set_value("to_warehouse", intermediate_warehouse);
                    }
                }
            });
    }
});

// function prepare_RAW(frm) {

//     toggle_fields(frm, true, 'source_warehouse', 'target_warehouse');
//     toggle_fields(frm, false, 'from_warehouse', 'to_warehouse');
//     reset_fields(frm, "", "from_warehouse", "to_warehouse",
//         "source_warehouse", "target_warehouse");
// }

function receive_at_warehouse(frm) {

    if (frm.doc.outgoing_stock_entry) {
        frappe.call({
            method: "custom_stock.common.stock_common.get_ongoing_stock_entry",
            args: {
                entry: frm.doc.outgoing_stock_entry
            },
            callback: (r) => {
                if (r.message) {
                    const _entry = r.message;

                    frappe.run_serially([
                        () => {

                            frm.set_value("from_warehouse", _entry.to_warehouse).then(() => {

                                frm.set_value("source_warehouse", _entry.source_warehouse).then(() => {
                                    frm.events.set_warehouse_acronym(frm, _entry.from_warehouse, "sw");
                                });
                            });
                            frm.set_value("target_warehouse", _entry.target_warehouse);
                        },
                        () => {
                            console.log(_entry.target_warehouse);
                            frm.set_value('to_warehouse', _entry.target_warehouse)
                                .then(() => {
                                    frm.set_df_property('target_warehouse', 'read_only', 1);
                                    frm.set_df_property('source_warehouse', 'read_only', 1);
                                });
                            frm.refresh_fields();

                        }
                    ]);
                }
            }
        });
    }
    else {
        reset_fields(frm, "", 'from_warehouse', 'to_warehouse', 'source_warehouse');
    }
}

function toggle_fields(context, flag) {

    for (let index = 2; index < arguments.length; index++) {
        const element = arguments[index];
        context.get_field(element).toggle(flag);
    }
}

function reset_fields(context, value) {

    for (let index = 2; index < arguments.length; index++) {
        const element = arguments[index];
        context.doc[element] = value;
    }
    context.refresh_fields();
}

function set_branch(frm, warhouse) {
    // if (warhouse) {
    frappe.call({
        method: "custom_stock.common.stock_common.get_warehouse_branch",
        args: {
            warehouse: warhouse
        },
        callback: (r) => {
            if (r.message) {
                const _warehouse = r.message;
                frm.set_value('branch', _warehouse.branch);
            }
        }
    });
    // }
}