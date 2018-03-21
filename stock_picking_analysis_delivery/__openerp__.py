# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
'name': 'stock_picking_analysis_delivery',
'version': '0.1',
'summary': 'Extended stock picking analysis with weight and carrier',
'category': 'stock',
'description': """Extended stock picking analysis with weight and carrier

    carrier_id, volume, weight, weight_net, number_of_packages

Report financed by Dermanord-Svensk Hudvård AB""",
'author': 'Vertel AB',
    'license': 'AGPL-3',
'website': 'http://www.vertel.se',
'depends': ['stock_picking_analysis','delivery'],
'data': [ 'stock_picking_report_view.xml',],
'installable': True,
'auto_install': True,
}
