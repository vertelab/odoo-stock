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
    'version': '14.0.1.0',
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

Calculated orderpoint are displayed for reordering rules minimum quantity.

The calculations are performed by a cron job. They can be very taxing if
there are many sale order lines. To avoid timeouts and other issues, the
job is set to run on 5 minute intervals, calculating up to 30 products,
or for a maximum duration of 4 minutes. A simple schedule is also
implemented, defaulting to between 00:00 and 06:00 in admin's timezone.
All three of these values can be configured through system parameters.

System Parameters
 * calc_orderpoint.schedule - A simple schedule. Space separated list of
start and stop hours, e.g. "0 4 18 24" (between 00:00 and 04:00, and
18:00 and 00:00)
 * calc_orderpoint.time_limit - The time limit in minutes. Float value.
 * calc_orderpoint.product_limit - The max number of products. Integer.
""",
    'author': 'Vertel AB',
    'license': 'AGPL-3',
    'website': 'http://www.vertel.se',
    'depends': ['stock', 'mrp', 'sale', 'point_of_sale'],
    'data': [
        'views/product_view.xml',
        'data/product_data.xml',
    ],
    'installable': True,
}

