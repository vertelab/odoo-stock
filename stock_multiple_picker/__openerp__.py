# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2016- Vertel AB (<http://vertel.se>).
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
'name': 'Stock Multiple Pickers',
'version': '0.1',
'summary': 'Extends Picking list with pickers',
'category': 'stock',
'description': """
    Wizard that distributes one or many pickers on a picking. Multiple persons can pick
    in parallell.


Financed by Dermanord-Svensk Hudvård AB""",
'author': 'Vertel AB',
'website': 'http://www.vertel.se',
'depends': ['stock', 'hr',],
'data': ['stock_view.xml', 'wizard/stock_picking_view.xml'],
'installable': True,
}
