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



class procurement_rule(models.Model):
    _inherit = 'procurement.rule'

    @api.model
    def _get_action(self,):
        return [('pick_by_bom', _('Pick by BOM'))] + super(procurement_rule, self)._get_action()

class procurement_order(models.Model):
    _inherit = 'procurement.order'
 

    #~ def propagate_cancel(self, cr, uid, procurement, context=None):
        #~ if procurement.rule_id.action == 'pick_by_bom' and procurement.production_id:
            #~ self.pool.get('mrp.production').action_cancel(cr, uid, [procurement.production_id.id], context=context)
        #~ return super(procurement_order, self).propagate_cancel(cr, uid, procurement, context=context)
    
    def X_assign(self, cr, uid, procurement, context=None):
        '''This method check what to do with the given procurement in order to complete its needs.
        It returns False if no solution is found, otherwise it stores the matching rule (if any) and
        returns True.
            :param procurement: browse record
            :rtype: boolean
        '''
        #if the procurement already has a rule assigned, we keep it (it has a higher priority as it may have been chosen manually)
        if procurement.rule_id:
            return True
        elif procurement.product_id.type == 'kit':
            procurement.rule_id = 10
            return True
        return super(procurement_order, self)._assign(procurement)
    
    @api.model    
    def Xrun(self,ids, autocommit=False):
        new_ids = [x.id for x in self.env['procurement.order'].browse(ids) if x.state not in ('running', 'done', 'cancel')]
        #~ raise Warning(new_ids,autocommit)
        for procurement in self.env['procurement.order'].browse(new_ids):
            if procurement.product_id.type == 'kit':
                procurement.rule_id = 10
        res = super(procurement_order, self).run(new_ids)
        return res
        
    @api.model
    def _run(self,procurement):
        #~ if procurement.rule_id and procurement.rule_id.action == 'pick_by_bom':
        res = super(procurement_order, self)._run(procurement)
        if procurement.product_id and procurement.product_id.type == 'kit':
            #~ raise Warning(self,procurement)
            res = {}
            bom_id = self.env['mrp.bom']._bom_find(product_id=procurement.product_id.id,properties=[x.id for x in procurement.property_ids])
            procurement.bom_id = bom_id
            if bom_id:
                for line in procurement.bom_id.bom_line_ids:
                    p = self.env['procurement.order'].create({
                        'name': procurement.name,
                        'origin': procurement.origin,
                        'company_id': procurement.company_id.id,
                        'priority': procurement.priority,
                        'date_planned': procurement.date_planned,
                        'group_id': procurement.group_id.id,
                        'location_id': procurement.location_id.id if procurement.location_id else False,
                        'warehouse_id': procurement.warehouse_id.id if procurement.warehouse_id else False,
                        'partner_dest_id': procurement.partner_dest_id.id if procurement.partner_dest_id else False,

                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        #~ 'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_qty,
                        #~ 'product_uos': (line.product_uos and line.product_uos.id) or line.product_uom.id,

                        'invoice_state': 'none',
                        'sale_line_id': procurement.sale_line_id.id,
                    })
                    _logger.warn('%s %s %s', (p.name,p.product_id.name, p.rule_id))
                    p.rule_id = self._find_suitable_rule(p) or False
                    p.run()
                res[procurement.id] = procurement.bom_id.id
                procurement.message_post(body=_("Procurement Order for BOM <em>%s</em> created.") % (procurement.bom_id.name,))
  
            else:
                res[procurement.id] = False
                procurement.message_post(body=_("No BoM exists for this product!"))
        return res
        

    @api.model
    def X_find_suitable_rule(procurement):
        product_route_ids = [x.id for x in procurement.product_id.route_ids + procurement.product_id.categ_id.total_route_ids]
        raise Warning(product_route_ids)
        if procurement.product_id.type == 'kit':
            #procurement.rule_id = 10
            return True
        return super(procurement_order, self)._find_suitable_rule(procurement)
    @api.model
    def _check(self,procurement):
        if procurement.product_id and procurement.product_id.type == 'kit' and procurement.state in ['draft',]:
            procurement.run_scheduler()
            return True
        return super(procurement_order, self)._check(procurement)


    #~ @api.model
    #~ def _prepare_mo_vals(self,procurement):
        #~ res_id = procurement.move_dest_id and procurement.move_dest_id.id or False
        #~ newdate = self._get_date_planned(cr, uid, procurement, context=context)
        #~ if procurement.bom_id:
            #~ bom_id = procurement.bom_id.id
            #~ routing_id = procurement.bom_id.routing_id.id
        #~ else:
            #~ properties = [x.id for x in procurement.property_ids]
            #~ bom_id = self.env['mrp.bom']._bom_find(product_id=procurement.product_id.id,properties=properties)
            #~ bom = self.env['mrp.bom'].browse(bom_id)
            #~ routing_id = bom.routing_id.id
        #~ return {
            #~ 'origin': procurement.origin,
            #~ 'product_id': procurement.product_id.id,
            #~ 'product_qty': procurement.product_qty,
            #~ 'product_uom': procurement.product_uom.id,
            #~ 'product_uos_qty': procurement.product_uos and procurement.product_uos_qty or False,
            #~ 'product_uos': procurement.product_uos and procurement.product_uos.id or False,
            #~ 'location_src_id': procurement.location_id.id,
            #~ 'location_dest_id': procurement.location_id.id,
            #~ 'bom_id': bom_id,
            #~ 'routing_id': routing_id,
            #~ 'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
            #~ 'move_prod_id': res_id,
            #~ 'company_id': procurement.company_id.id,
        #~ }



    def X_run_move_create(self, cr, uid, procurement, context=None):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        newdate = (datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.rule_id.delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
        group_id = False
        if procurement.rule_id.group_propagation_option == 'propagate':
            group_id = procurement.group_id and procurement.group_id.id or False
        elif procurement.rule_id.group_propagation_option == 'fixed':
            group_id = procurement.rule_id.group_id and procurement.rule_id.group_id.id or False
        #it is possible that we've already got some move done, so check for the done qty and create
        #a new move with the correct qty
        already_done_qty = 0
        already_done_qty_uos = 0
        for move in procurement.move_ids:
            already_done_qty += move.product_uom_qty if move.state == 'done' else 0
            already_done_qty_uos += move.product_uos_qty if move.state == 'done' else 0
        qty_left = max(procurement.product_qty - already_done_qty, 0)
        qty_uos_left = max(procurement.product_uos_qty - already_done_qty_uos, 0)
        vals = {
            'name': procurement.name,
            'company_id': procurement.rule_id.company_id.id or procurement.rule_id.location_src_id.company_id.id or procurement.rule_id.location_id.company_id.id or procurement.company_id.id,
            'product_id': procurement.product_id.id,
            'product_uom': procurement.product_uom.id,
            'product_uom_qty': qty_left,
            'product_uos_qty': (procurement.product_uos and qty_uos_left) or qty_left,
            'product_uos': (procurement.product_uos and procurement.product_uos.id) or procurement.product_uom.id,
            'partner_id': procurement.rule_id.partner_address_id.id or (procurement.group_id and procurement.group_id.partner_id.id) or False,
            'location_id': procurement.rule_id.location_src_id.id,
            'location_dest_id': procurement.location_id.id,
            'move_dest_id': procurement.move_dest_id and procurement.move_dest_id.id or False,
            'procurement_id': procurement.id,
            'rule_id': procurement.rule_id.id,
            'procure_method': procurement.rule_id.procure_method,
            'origin': procurement.origin,
            'picking_type_id': procurement.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, x.id) for x in procurement.route_ids],
            'warehouse_id': procurement.rule_id.propagate_warehouse_id.id or procurement.rule_id.warehouse_id.id,
            'date': newdate,
            'date_expected': newdate,
            'propagate': procurement.rule_id.propagate,
            'priority': procurement.priority,
        }
        return vals

class product_template(models.Model):
    _inherit = "product.template"

    type = fields.Selection(selection_add=[('kit','Kit')])
        
class product_product(models.Model):
    _inherit = "product.product"  
    @api.multi
    def name_get(self):
        res = super(product_product, self).name_get()
        result = []
        for r in res:
            product = self.env['product.product'].browse(int(r[0]))
            if product.type == 'kit':
                result.append([product.id, "[%s] %s (kit)" % (product.default_code, product.name)])
            else:
                result.append(r)
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
