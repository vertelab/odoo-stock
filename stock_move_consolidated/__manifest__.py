# -*- coding: utf-8 -*-
{
    'name': "Consolidate Stock Moves",
    'summary': """Consolidate Stock Moves""",
    'description': """Consolidate Stock Moves""",
    'author': "Vertel",
    'website': "vertel.se",
    'category': 'stock',
    'version': '14.0.0.0.1',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_move_history_view.xml',
        'views/template.xml',
    ],
    'qweb': [
        'static/src/xml/stock_move_report.xml',
    ],

}
