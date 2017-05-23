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
    'name': 'Calculate Orderpoint',
    'version': '0.1',
    'category': 'stock',
    'description': """
Calculates 
 * consumtion_per_day  (How many items consumes per day)
 * orderpoint_computed (consumtion_per_day * delay)
 * virtual_available_days  (How many days will stock be available)

delay is calculated by sellers delay + po lead for the company or 
produce_delay + the company manufacturing lead.

Consumtion per day are calculated from number of days the product has
been sold (up to a year) and how many items sold during the same period.

Calculated orderpoint are displayed for reordering rules minimum quantity
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['website_sale','stock'],
    'data': [
        'product_view.xml',
    ],
    'installable': True,
}

