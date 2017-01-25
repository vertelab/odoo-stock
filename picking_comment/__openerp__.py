# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2017- Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
'name': 'Picking Comment',
'version': '0.1',
'summary': 'Comment on picking slip',
'category': 'stock',
'description': """
    Adds a comment on picking rows with special instructions for the picker.
    
    * Adds a picking comment on product.product
    * Views the comment on picking
    * Views the comment on barecode gui
    
Financed by Dermanord-Svensk Hudvård AB""",
'author': 'Vertel AB',
'website': 'http://www.vertel.se',
'depends': ['stock',],
'data': ['product_view.xml', 'stock_picking_report.xml'],
'installable': True,
}
