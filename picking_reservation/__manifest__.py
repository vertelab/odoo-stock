# -*- coding: utf-8 -*-
{
    'name': "picking_reservation",

    'summary': """
    When a locations need to use a pull move to satiate an order, now it won't reserve the exact products moved. It will go after fifo or lifo for all products.
    """,

    'description': """
        When a locations need to use a pull move to satiate an order, now it won't reserve the exact products moved. It will go after fifo or lifo for all products.                                                       
    """,

    'author': "Vertel",
    'website': "Vertel.se",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

}
