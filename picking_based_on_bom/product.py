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

import openerp.exceptions
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class product_product(models.Model):
    _inherit="product.product"

    is_bom_picking = fields.Boolean(String='Pick based on BOM', help="This product will be picked as ")

class procurement_rule(models.Model):
    _inherit = 'procurement.rule'

    @api.model
    def _get_action(self,):
        return [('pick_by_bom', _('Pick by BOM'))] + super(procurement_rule, self)._get_action()

    #~ def propagate_cancel(self, cr, uid, procurement, context=None):
        #~ if procurement.rule_id.action == 'pick_by_bom' and procurement.production_id:
            #~ self.pool.get('mrp.production').action_cancel(cr, uid, [procurement.production_id.id], context=context)
        #~ return super(procurement_order, self).propagate_cancel(cr, uid, procurement, context=context)

    def _run(self, cr, uid, procurement, context=None):
        if procurement.rule_id and procurement.rule_id.action == 'pick_by_bom':
            #make a manufacturing order for the procurement
            return self.make_mo(cr, uid, [procurement.id], context=context)[procurement.id]
        return super(procurement_order, self)._run(cr, uid, procurement, context=context)

    def _check(self, cr, uid, procurement, context=None):
        if procurement.production_id and procurement.production_id.state == 'done':  # TOCHECK: no better method? 
            return True
        return super(procurement_order, self)._check(cr, uid, procurement, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
