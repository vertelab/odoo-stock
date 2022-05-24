# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Stock Barcode Alternative - Unifaun',
    'version': '14.0.1.0',
    'summary': 'Unifaun functionality for the alternative barcode scanning interface.',
    'description': """
Stock Barcode Alternative Unifaun
================================
Adds Unifaun functionality to the alternative barcode interface.
    """,
    'category': 'website',
    'website': 'http://www.vertel.se',
    'author': 'Vertel AB',
    'depends': ['stock_barcode_alternative', 'delivery_unifaun_base'],
    'data': [
        'views/stock_view.xml',
    ],
    'demo': [],
    'qweb': ['static/src/xml/picking.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}