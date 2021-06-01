# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock Barcode Alternative',
    'version': '14.0.1.0',
    'summary': 'Alternative barcode scanning interface.',
    'description': """
Stock Barcode Alternative
================================
Alternative barcode scanning interface that accomplishes most things in the browser, \n
thus speeding up the process.
    """,
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'category': 'website',
    'depends': ['stock', 'website'],
    'data': [
        'views/assets.xml',
        'views/stock_view.xml',
        'views/barcode_index.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'static/src/xml/picking.xml'
    ],
}
