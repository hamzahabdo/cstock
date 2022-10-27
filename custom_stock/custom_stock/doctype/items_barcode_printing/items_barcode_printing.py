# -*- coding: utf-8 -*-
# Copyright (c) 2020, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import math
from frappe.model.document import Document
from erpnext.stock.utils import get_latest_stock_qty


class ItemsBarcodePrinting(Document):
    pass


@frappe.whitelist()
def get_all_items(source_type, source_name, price_list, branch):
    source = frappe.get_doc(source_type, source_name)
    items = []
    for item in source.items:
        if(source_type == "Discount Batch"):
            warehouse = frappe.get_doc('Warehouse', {'branch': branch})
            qty = get_latest_stock_qty(item.item_code, warehouse.name)
        else:
            qty = item.qty
        i = get_item(item.item_code, price_list, qty)
        items.append(i)

    return items


@frappe.whitelist()
def get_single_item(item_code, branch, price_list):

    if item_code:

        item = get_item(item_code, price_list)

        warehouse = frappe.get_doc('Warehouse', {'branch': branch})

        qty = get_latest_stock_qty(item_code, warehouse.name)

        item['quantity'] = qty

        return item
    else:
        pass


def get_item(item_code, price_list, qty=""):

    items = frappe.get_list('Item Price',
                            fields=['item_code', 'item_name',
                                    'price_list_rate', 'previous_rate'],
                            filters={'item_code': item_code,
                                     'price_list': price_list},
                            order_by='valid_from desc',
                            limit_page_length=1)

    if items:
        barcode = get_item_barcode(items[0].item_code)
        items_list = {
            'item': items[0].item_code,
            'item_name': items[0].item_name,
            'item_price': items[0].price_list_rate,
            'previous_price': items[0].previous_rate,
            'percentage_change': get_percentage_change(items[0].previous_rate, items[0].price_list_rate),
            'barcode': barcode,
            'quantity': qty,
        }
    else:
        items_list = {
            'item': "",
            'item_name': "",
            'item_price': "",
            'previous_price': "",
            'percentage_change': "",
            'barcode': "",
            'quantity': "",
        }

    return items_list


def get_percentage_change(previous_rate, current_rate):
    if previous_rate:
        return math.floor(((previous_rate - current_rate) / previous_rate) * 100)
    else:
        return 0


def get_item_barcode(item_code):
    barcode = frappe.get_doc('Item', item_code)
    if barcode.barcodes:
        return barcode.barcodes[0].barcode
    return ""


@frappe.whitelist()
def get_printer_layouts(printer):
    printer_model = frappe.get_doc('Barcode Printer Type', printer)
    layouts = []
    for layout in printer_model.layouts:
        layouts.append(layout.layout)

    return layouts


@frappe.whitelist()
def get_markup_layout(model, layout):
    printer_model = frappe.get_doc('Barcode Printer Type', model)
    if printer_model:
        for l in printer_model.layouts:
            if l.layout == layout:
                print_layout = l
                print_markup = frappe.get_doc('Layout Markup', layout)

                return print_layout, print_markup
    return False
