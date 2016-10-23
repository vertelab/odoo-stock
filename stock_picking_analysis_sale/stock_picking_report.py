# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, Open Source Management Solution, third party addon
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

from openerp import tools
from openerp import models, fields, api, _

import openerp.addons.decimal_precision as dp

class stock_picking_report(models.Model):
    _inherit = "stock_picking.report"
    
    sale_id = fields.Many2one(comodel_name="sale.order",string="Order",readonly=True)
    nbr_orders = fields.Integer(string='# of Orders', readonly=True)

    def _select(self):
        return  super(stock_picking_report, self)._select() + """, sale_order.id as sale_id,
        count(sale_order.*) as nbr_orders"""

    def _group_by(self):
        return super(stock_picking_report, self)._group_by() + ", sale_order.id"

    def _from(self):
        return super(stock_picking_report, self)._from() + "left join sale_order on (sp.group_id = sale_order.procurement_group_id)\n"
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
