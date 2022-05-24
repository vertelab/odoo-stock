# -*- coding: utf-8 -*-
{
    'name': "stock_location_priority",

    'summary': """
        Added a fipo rule that allows prioritization of locations
        """,

    'description': """
        Added a fipo rule that allows prioritization of locations
    """,

    'author': "Vertel AB",
    'website': "vertel.se",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'data/data.xml',
        'views/views.xml',
    ],

}
