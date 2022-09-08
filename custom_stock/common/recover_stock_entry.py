import frappe
from frappe import _
from erpnext.accounts.general_ledger import make_reverse_gl_entries


@frappe.whitelist()
def recover_stock_entry(between_branches=False, to_date='', deploy_changes=False):
    stock_entry_transactions = get_stock_entry_transactions(
        between_branches, to_date)
    if not between_branches:
        current_accoutn_in_gle = check_current_account_in_gle(
            stock_entry_transactions, deploy_changes)
        return current_accoutn_in_gle
    else:
        current_account_between_branches_in_gle = check_current_account_between_branches_in_gle(
            stock_entry_transactions, deploy_changes)
        return current_account_between_branches_in_gle


@frappe.whitelist()
def get_stock_entry_transactions(between_branches=False, to_date=''):
    all_transactions = frappe.get_list("Stock Entry", fields=['name', 'purpose', 'source_warehouse', 'target_warehouse', 'add_to_transit', 'outgoing_stock_entry'], filters={
        'purpose': 'Material Transfer', 'posting_date': ['<=', to_date], 'docstatus': 1})

    chosen_transactions = []
    for transaction in all_transactions:
        if(transaction.source_warehouse and transaction.target_warehouse):
            # print(transaction.source_warehouse,transaction.target_warehouse)
            source_current_warehouse = get_current_account(
                transaction.source_warehouse)
            target_current_warehouse = get_current_account(
                transaction.target_warehouse)

            if between_branches:
                if(source_current_warehouse != target_current_warehouse):
                    if transaction.outgoing_stock_entry:
                        transaction['current_warehouse'] = source_current_warehouse
                    else:
                        transaction['current_warehouse'] = target_current_warehouse
                    # print(source_current_warehouse,target_current_warehouse)
                    chosen_transactions.append(transaction)

            else:
                if (transaction.add_to_transit or transaction.outgoing_stock_entry):
                    if(source_current_warehouse == target_current_warehouse):
                        transaction['current_warehouse'] = source_current_warehouse
                        # print(source_current_warehouse,target_current_warehouse)
                        chosen_transactions.append(transaction)

    return chosen_transactions


def get_current_account(warehouse):
    branch = frappe.get_doc('Warehouse', warehouse).branch
    return frappe.get_doc('Branch', branch).currant_account


def fix_gl_entry_for_stock_entry(voucher_no_for_se, deploy_changes):
    if(deploy_changes):
        make_reverse_gl_entries(
            voucher_type='Stock Entry', voucher_no=voucher_no_for_se)
        se_doc = frappe.get_doc('Stock Entry', voucher_no_for_se)
        frappe.call(getattr(se_doc, "make_gl_entries"),
                    **frappe.local.form_dict)

    print("no changes")
    pass


def check_current_account_in_gle(transactions, deploy_changes):
    stock_entries = []
    for transaction in transactions:
        gl_entry_list = frappe.get_all('GL Entry', fields=['name', 'account', 'voucher_no', 'posting_date'], filters={
            'is_cancelled': 0, 'voucher_no': transaction.name})

        # exist_gl_entries = []
        for gl_entry in gl_entry_list:
            if(gl_entry.account == transaction.current_warehouse):
                stock_entries.append(transaction.name)
                fix_gl_entry_for_stock_entry(
                    gl_entry.voucher_no, deploy_changes)

    print(len(stock_entries), '000000000', len(transactions))
    return stock_entries


def check_current_account_between_branches_in_gle(transactions, deploy_changes):

    from custom_stock.common.stock_common import get_gl_entries as custom_get_gl_entries
    from erpnext.controllers.stock_controller import StockController
    StockController.get_gl_entries = custom_get_gl_entries

    i = 0
    stock_entries = []
    current_stock_entries = []

    for transaction in transactions:
        gl_entry_list = frappe.get_all('GL Entry', fields=['name', 'account', 'voucher_no', 'posting_date'], filters={
                                       'is_cancelled': 0, 'voucher_no': transaction.name})

        exist_gl_entries = []
        exist_current_warehouse = 0
        for gl_entry in gl_entry_list:
            exist_gl_entries = gl_entry_list
            if(gl_entry.account == transaction.current_warehouse):
                print(gl_entry.account, gl_entry.name, transaction.name)
                exist_current_warehouse = 1
                current_stock_entries.append(transaction)
                i += 1

        if not exist_current_warehouse:
            stock_entries.append(transaction.name)
            fix_gl_entry_for_stock_entry(transaction.name, deploy_changes)

    # print(len(stock_entries),'000000000',len(transactions),len(current_stock_entries))
    return stock_entries


# frappe.call({
#     method: 'custom_stock.common.recover_stock_entry.recover_stock_entry',
#     args: {between_branches:false ,to_date:'2022-08-20',deploy_changes:False},

#     freeze: true,
#     callback: (r) => {
#         console.log(r)
#     },
#     error: (r) => {
#          console.log(r)
#     }
# })
