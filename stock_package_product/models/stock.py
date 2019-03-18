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
from odoo import models, fields, api, _
from openerp.exceptions import ValidationError
import math

import logging
_logger = logging.getLogger(__name__)

class ProductProductPackageLine(models.Model):
    _name = 'product.product.package.line'
    
    package_product_id = fields.Many2one(string='Package Product', comodel_name='product.product', required=True, ondelete='cascade')
    product_id = fields.Many2one(string='Product', comodel_name='product.product', required=True, ondelete='cascade')
    qty = fields.Float('Quantity', required=True, default=1)
    uom_id = fields.Many2one(string='Unit', comodel_name='product.uom', required=True)
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    package_product_ids = fields.One2many(string='Package Products', comodel_name='product.product.package.line', inverse_name='package_product_id')
    is_package_product = fields.Boolean(string='Package Product')
    
    @api.one
    @api.constrains('is_package_product', 'package_product_ids')
    def _check_package_procurement_ids(self):
        if self.is_package_product and not self.package_product_ids:
            raise ValidationError("A package product must have content!")
    
    @api.multi
    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super(ProductProduct, self)._compute_quantities_dict(lot_id, owner_id, package_id, from_date=from_date, to_date=to_date)
        for product in self:
            if product.is_package_product:
                p_av = res[product.id]
                first = True
                for line in product.package_product_ids:
                    c_av = line.product_id._compute_quantities_dict(lot_id, owner_id, package_id, from_date=from_date, to_date=to_date)[line.product_id.id]
                    for key in c_av:
                        available = c_av[key] / line.uom_id._compute_quantity(line.qty, line.product_id.uom_id)
                        available = float(int(available))
                        if first or (available < p_av[key]):
                            p_av[key] = available
                    first = False
        return res

class ProcurementOrder(models.Model):
    _inherit = "procurement.order"
    
    package_procurement_id = fields.Many2one(string='Parent Package Procurement', comodel_name='procurement.order', ondelete='cascade')
    package_procurement_ids = fields.One2many(string='Package Content Procurements', comodel_name='procurement.order', inverse_name='package_procurement_id')
    
    @api.multi
    def _run(self):
        if self.rule_id.action == 'move' and self.product_id.is_package_product:
            for line in self.product_id.package_product_ids:
                procurement = self.env['procurement.order'].create({
                    'name': self.name,
                    'package_procurement_id': self.id,
                    'origin': self.origin,
                    'company_id': self.company_id.id,
                    'priority': self.priority,
                    'date_planned': self.date_planned,
                    'group_id': self.group_id and self.group_id.id or False,
                    
                    'location_id': self.location_id and self.location_id.id or False,
                    'warehouse_id': self.warehouse_id and self.warehouse_id.id or False,
                    'partner_dest_id': self.partner_dest_id and self.partner_dest_id.id or False,

                    'product_id': line.product_id.id,
                    'product_qty': line.qty * self.product_qty,
                    'product_uom': line.uom_id.id,

                    'invoice_state': 'none',
                    'sale_line_id': self.sale_line_id and self.sale_line_id.id or False,
                })
                procurement.message_post(body=_("Procurement Order created from package <em>%s</em>.") % (self.product_id.name_get()[0][1]))
            return True
        return super(ProcurementOrder, self)._run()
    
    @api.multi
    @api.returns('self', lambda procurements: [procurement.id for procurement in procurements])
    def check(self, autocommit=False):
        # Check if any of the procurements belong to a package and check status of package procurements.
        procurements_done = super(ProcurementOrder, self).check(autocommit=autocommit)
        parents = procurements_done.mapped('package_procurement_id')
        if parents:
            parents.check(autocommit=autocommit)
        return procurements_done
    
    @api.multi
    def _check(self):
        # Check status for package products.
        if self.rule_id.action == 'move' and self.product_id.is_package_product:
            if all(proc.state == 'cancel' for proc in self.package_procurement_ids):
                self.write({'state': 'cancel'})
                return False
            elif all(proc.state in ('done', 'cancel') for proc in self.package_procurement_ids):
                return True
            return False
        return super(ProcurementOrder, self)._check()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # TODO: Fix this function
    # ~ @api.multi
    # ~ def _get_delivered_qty(self):
        # ~ """Computes the delivered quantity on sale order lines, based on done stock moves related to its procurements
        # ~ """
        # ~ self.ensure_one()
        # ~ qty = super(SaleOrderLine, self)._get_delivered_qty()
        # ~ parent_procurements = self.procurement_ids.mapped('package_procurement_id')
        # ~ if parent_procurements:
            # ~ qty = 0.0
            # ~ qtys_expected = {}
            # ~ qtys = {}
            # ~ package_product_ids = set()
            # ~ for procurement in parent_procurements:
                # ~ package_product_ids.add(procurement.product_id.id)
                # ~ # Convert quantity from procurement unit to product unit
                # ~ procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_id)
                # ~ for line in procurement.package_procurement_ids:
                    # ~ if line.product_id.id not in qtys_expected:
                        # ~ qtys_expected[line.product_id.id] = 0.0
                    # ~ qtys_expected[line.product_id.id] += line.uom_id._compute_quantity(line.qty, line.product_id.uom_id) * procurement_qty
            # ~ child_procurements = self.procurement_ids.filtered(lambda p: p.product_id.id not in package_product_ids)
            # ~ for procurement in child_procurements:
                # ~ procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_id)
                # ~ if procurement.product_id.id not in qtys:
                    # ~ qtys[procurement.product_id.id] = 0.0
                # ~ for move in procurement.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
                    # ~ if move.product_id.id not in qtys:
                        # ~ qtys[move.product_id.id] = 0.0
                    # ~ if move.location_dest_id.usage == "customer":
                        # ~ # FORWARD-PORT NOTICE: "to_refund_so" to rename to "to_refund" in v11
                        # ~ if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund_so):
                            # ~ qtys[move.product_id.id] += move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id)
                    # ~ elif move.location_dest_id.usage != "customer" and move.to_refund_so:
                        # ~ qtys[move.product_id.id] -= move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id)
                
        # ~ for move in self.procurement_ids.mapped('move_ids').filtered(lambda r: r.state == 'done' and not r.scrapped):
            # ~ if move.location_dest_id.usage == "customer":
                # ~ # FORWARD-PORT NOTICE: "to_refund_so" to rename to "to_refund" in v11
                # ~ if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund_so):
                    # ~ qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
            # ~ elif move.location_dest_id.usage != "customer" and move.to_refund_so:
                # ~ qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
        # ~ return qty
