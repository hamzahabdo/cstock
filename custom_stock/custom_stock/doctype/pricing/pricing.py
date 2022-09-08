# -*- coding: utf-8 -*-
# Copyright (c) 2020, BM and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from warnings import filters
import frappe
from frappe import _, whitelist
import math
from frappe.model.document import Document
from datetime import datetime
# from nct.ncity.page.item_board.item_board import get_last_purchase_rate_from_price_list


class PriceLowerThanValuationError(frappe.ValidationError):
    def __init__(self):
        self.message = "Price cannot be lower than Valuation Rate"
        super(frappe.ValidationError, self).__init__(self.message)


class Pricing(Document):
    def save(self, *args, **kwargs):
        for item in self.items:
            doc = frappe.get_doc({
                'doctype': 'Item Price',
                'item_code': item.item,
                'price_list': item.price_list,
                'price_list_rate': item.rate,
                'minimum_rate': item.minimum_rate,
                'valid_from': self.date
            })
            doc.insert()

        for item in self.priced_items:
            item_name = item.item_price

            if item.item_price:
                frappe.set_value('Item Price', item_name,
                                 'price_list_rate', item.rate)
            if item.minimum_rate:
                frappe.set_value('Item Price', item_name,
                                 'minimum_rate', item.minimum_rate)

        super().save(*args, **kwargs)
    @whitelist()
    def get_prices(self, source_name, source_type, price_lists, is_ratio, min_rate_is_ratio):
        source = frappe.get_doc(source_type, source_name)
        items = []
        for price_list in price_lists:
            for item in source.items:
                items.append(self.get_item(item, source_type, source,
                                           price_list["price_list"], price_list["ratio"], is_ratio, min_rate_is_ratio, price_list["minimum__rate"]))
        return items

    def get_item(self, item, source_type, source, price_list, ratio, is_ratio, min_rate_is_ratio, minimum__rate):

        # last_price = frappe.db.get_list('Item Price', fields=['max(valid_from) as valid_from'], filters={
        #                           'item_code': item.item_code, 'price_list': price_list})

        # item_prices = frappe.db.get_list('Item Price', fields=['name', 'price_list_rate', 'minimum_rate'],
        #                            filters={'item_code': item.item_code, 'price_list': price_list})

        last_price = self.get_last_price(item.item_code, price_list)

        item_rate = 0
        if source_type == 'Stock Entry':
            item_rate = item.basic_rate
            valuation = item_rate
        elif source_type == 'Discount Batch':
            item_rate = item.new_price
            from erpnext.stock.get_item_details import get_valuation_rate
            default_company = frappe.db.get_single_value(
                'Global Defaults', 'default_company')
            item_valuation = get_valuation_rate(
                item.item_code, default_company, source.warehouse)
            valuation = item_valuation["valuation_rate"]

        else:
            item_rate = item.rate
            valuation = item_rate
        if not last_price:
            if is_ratio == 1:
                rate = math.ceil(ratio * item_rate / 100 + item_rate)
            else:
                rate = math.ceil(ratio + item_rate)
            if min_rate_is_ratio == 1:
                item_minimum_rate = math.ceil(
                    minimum__rate * item_rate / 100 + item_rate)
            else:
                item_minimum_rate = math.ceil(minimum__rate + item_rate)

            return {
                'item': item.item_code,
                'item_name': item.item_name,
                'price_list': price_list,
                'valuation': valuation,
                'rate': rate,
                'minimum_rate': item_minimum_rate,
                'priced': False
            }
        if(source_type == 'Discount Batch'):
            rate = item_rate
            minimum_rate = item_rate
        else:
            # items[0].price_list_rate,
            rate = last_price.price_list_rate
            minimum_rate = last_price.minimum_rate
        return {
            'item': item.item_code,
            'item_name': item.item_name,
            'price_list': price_list,
            'valuation': valuation,
            'rate': rate,
            'minimum_rate': minimum_rate,
            'priced': True,
            'item_price': last_price.name
        }

    def get_last_price(self, item_code, price_list):
        last_date_price = frappe.db.get_list('Item Price', fields=['max(valid_from) as valid_from'],
                                             filters={'item_code': item_code, 'price_list': price_list, 'valid_from': ['<=', datetime.now()]})

        item_price = frappe.db.get_list('Item Price', fields=['name', 'price_list_rate', 'minimum_rate'],
                                        filters={'item_code': item_code, 'valid_from': last_date_price[0].valid_from, 'price_list': price_list})

        if(item_price):
            return item_price[0]
        return None


def set_previous_rate(doc, method):
    doc_before_save = doc.get_doc_before_save()
    if doc_before_save:
        if doc.price_list_rate != doc_before_save.price_list_rate:
            previous_rate = doc_before_save.price_list_rate
        else:
            previous_rate = doc_before_save.previous_rate
    else:
        previous_rate = get_last_rate(doc)

    doc.previous_rate = previous_rate if previous_rate else 0


def get_last_rate(doc):
    return frappe.db.get_value('Item Price', {
        'item_code': doc.item_code, 'price_list': doc.price_list, 'valid_from': ['<', doc.valid_from]}, 'price_list_rate', order_by='valid_from desc')


def validate_price_rate(doc, method):
    settings = frappe.get_doc('NCITY Settings')
    user_roles = frappe.get_roles(frappe.session.user)

    if settings.prevent_low_pricing and settings.pricing_role not in user_roles:
        try:
            validated_value = get_minimum_pricing_rate(
                doc.item_code, settings.pricing_percentage)
            if doc.price_list_rate < validated_value:
                raise PriceLowerThanValuationError()
        except PriceLowerThanValuationError as e:
            frappe.throw(_(e.message))
        except Exception as e:
            frappe.log_error(e, 'Item Price')
            frappe.throw(
                _("Something went wrong. Please contact your administrator."))


def get_minimum_pricing_rate(item_code, pricing_percentage):
    return calculate_minimum_pricing_rate(pricing_percentage, get_last_purchase_rate(item_code))


def calculate_minimum_pricing_rate(percentage, valuation_value):
    return valuation_value * (percentage / 100 + 1)


def get_last_purchase_rate(item_code):
    return frappe.db.get_value('Purchase Order Item', {
        'item_code': item_code}, 'base_rate') or 0
