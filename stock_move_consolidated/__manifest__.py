# -*- coding: utf-8 -*-
{
    'name': "stock_location_priority",
    'summary': """Added a fipo rule that allows prioritization of locations""",
    'description': """Added a fipo rule that allows prioritization of locations""",
    'author': "Vertel",
    'website': "vertel.se",
    'category': 'stock',
    'version': '14.0.0.0.1',
    'depends': ['base', 'stock'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/stock_move_line_view.xml',
        'wizard/stock_move_history_view.xml',
        'views/template.xml',
    ],
    'qweb': [
        'static/src/xml/stock_move_report.xml',
    ],

}
