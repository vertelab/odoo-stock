# -*- coding: utf-8 -*-
##############################################################################
#
#  Odoo, Open Source Enterprise Resource Management Solution, third party addon
#  Copyright (C) 2019- Vertel AB (<http://vertel.se>).
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Stock Barcode Alternative - Unifaun',
    'version': '8.0.1.0',
    'summary': 'Unifaun functionality for the alternative barcode scanning interface.',
    'description': """
Stock Barcode Alternative Unifaun
================================
Adds Unifaun functionality to the alternative barcode interface.
    """,
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'category': 'website',
    'sequence': 0,
    'depends': ['stock_barcode_alternative'],
    'demo': [],
    'data': [
        'views/stock_view.xml',
    ],
    'installable': True,
    # ~ 'qweb': ['static/src/xml/picking.xml'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
