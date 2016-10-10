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
    
    carrier_id = fields.Many2one(comodel_name="delivery.carrier",string="Carrier",readonly=True)
    volume = fields.Float(string='Volume',digits_compute=dp.get_precision('Stock Volume'),readonly=True)
    weight = fields.Float(string='Weight',digits_compute= dp.get_precision('Stock Weight'),readonly=True)
    weight_net = fields.Float(string='Net Weight',digits_compute= dp.get_precision('Stock Weight'),readonly=True)
    number_of_packages = fields.Integer(string='Number of Packages', readonly=True)

    def _select(self):
        return  super(stock_picking_report, self)._select() + ", s.carrier_id as carrier_id,  s.volume as volume, s.weight as weight, s.weight_net as weight_net, s.number_of_packages as number_of_packages"

    def _group_by(self):
        return super(stock_picking_report, self)._group_by() + ", s.carrier_id,  s.volume, s.weight, s.weight_net, s.number_of_packages"

    def _from(self):
        return super(stock_picking_report, self)._from() + "left join delivery_carrier on (s.carrier_id = delivery_carrier.id)\n"
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: