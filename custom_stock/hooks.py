from . import __version__ as app_version

app_name = "custom_stock"
app_title = "Custom Stock"
app_publisher = "burjalmaha"
app_description = "Custom Stock"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@burjalmaha.com"
app_license = "BM"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/custom_stock/css/custom_stock.css"
# app_include_js = "/assets/custom_stock/js/custom_stock.js"

# include js, css files in header of web template
# web_include_css = "/assets/custom_stock/css/custom_stock.css"
# web_include_js = "/assets/custom_stock/js/custom_stock.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "custom_stock/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Stock Entry": [
        "public/js/intermediate_account.js",
        "public/js/stock_entry_items.js",
        "public/js/stock_common.js",
        "public/js/custom_stock_entry.js"
    ],
    "Stock Reconciliation": "public/js/stock _reconciliation.js",
    "Item": "public/js/item_common.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "custom_stock.install.before_install"
# after_install = "custom_stock.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "custom_stock.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
    "Stock Entry": {
        # "on_submit": "custom_stock.common.stock_common.make_current_account_entries",
        "on_cancel": "custom_stock.common.stock_common.check_future_transactions",
        "before_save": "custom_stock.common.custom_stock_entry.CheckConversionFactor",
        "validate": [
                     "custom_stock.common.stock_common.validate_add_to_transit",
                     "custom_stock.common.stock_common.assign_override_methods",
                     "custom_stock.common.stock_common.validate_stock_keeper",
                     "custom_stock.common.stock_common.set_branch",
                     "custom_stock.common.stock_common.validate_for_items"
        ]
    },
    "Purchase Receipt": {
        "validate": "custom_stock.common.stock_common.assign_override_methods",
        "on_cancel": "custom_stock.common.stock_common.assign_override_methods",
        "before_save": "custom_stock.common.stock_common.CheckConversionFactor"
    },
    "Purchase Invoice": {
        "validate": "custom_stock.common.stock_common.assign_override_methods",
        "on_cancel": "custom_stock.common.stock_common.assign_override_methods"
    },
    "Purchase Order": {
        "before_save": "custom_stock.common.stock_common.CheckConversionFactor"
    },
    "Material Request": {
        "before_save": "custom_stock.common.stock_common.CheckConversionFactor"
    },
    "Stock Ledger Entry": {
        "before_save": "custom_stock.common.custom_stock_ledger_entry.check_actual_qty"
    },
    "RMS Stock Inventory": {
        "before_save": "custom_stock.common.stock_common.CheckConversionFactor"
    },
    "Item Price": {
        "validate": "custom_stock.custom_stock.doctype.pricing.pricing.validate_price_rate",
        "before_save": "custom_stock.custom_stock.doctype.pricing.pricing.set_previous_rate"
    },
    "Item": {
        "validate": [
            "custom_stock.common.stock_common.validate_item_code_and_barcodes",
            "custom_stock.common.barcode_generator.set_barcode"
        ]
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"custom_stock.tasks.all"
# 	],
# 	"daily": [
# 		"custom_stock.tasks.daily"
# 	],
# 	"hourly": [
# 		"custom_stock.tasks.hourly"
# 	],
# 	"weekly": [
# 		"custom_stock.tasks.weekly"
# 	]
# 	"monthly": [
# 		"custom_stock.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "custom_stock.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "custom_stock.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "custom_stock.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {
        "doctype": "{doctype_4}"
    }
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"custom_stock.auth.validate"
# ]
