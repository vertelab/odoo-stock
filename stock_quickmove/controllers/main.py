# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2019- Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.addons.web import http
from openerp.http import request, Response
import simplejson
import logging
_logger = logging.getLogger(__name__)

class StockSquickMove(http.Controller):

    @http.route(['/stock/quickmove', '/stock/quickmove/picking/<model("stock.picking"):picking>','/stock/quickmove/pickingtype/<model("stock.picking.type"):picking_type_id>'], type='http', auth='user', website=True)
    def stock_quickmove(self, picking=None, picking_type_id = None, **post):
        if request.httprequest.method == 'POST':
            _logger.warn(post)
            description = post.get('description')
            picking_type_id = picking_type_id or post.get('picking_type_id')
            if not picking_type_id:
                picking_type_id = request.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
            location_src_id = post.get('location_src_id')
            location_dest_id = post.get('location_dest_id')
            # if description and picking_type_id and location_src_id and location_dest_id:
            if picking_type_id and location_src_id and location_dest_id:
                picking_type_id = int(picking_type_id)
                location_src_id = int(location_src_id)
                location_dest_id = int(location_dest_id)
                if not picking:
                    picking = request.env['stock.picking'].create({
                        'picking_type_id': picking_type_id,
                    })
                    if description:
                        picking.name = '%s - %s' % (picking.name, description)
                    for k, v in post.items():
                        if k.startswith('total_qty_'):
                            product = request.env['product.product'].browse(int(k.split('_')[-1]))
                            request.env['stock.move'].create({
                                'product_id': product.id,
                                'name': product.name,
                                'product_uom_qty': float(int(v)),
                                'product_uom': product.uom_id.id,
                                'location_id': location_src_id,
                                'location_dest_id': location_dest_id,
                                'picking_id': picking.id
                            })
                else:
                    # update move lines
                    for k,v in post.items():
                        if k.startswith('product_qty_'):
                            product = request.env['product.product'].browse(int(k.split('_')[-1]))
                            move = picking.move_lines.with_context(product_id=product.id).filtered(lambda l: l.product_id.id == l._context.get('product_id'))
                            if move:
                                move.write({
                                    'name': product.name,
                                    'product_uom_qty': float(int(v)),
                                    'product_uom': product.uom_id.id,
                                    'location_id': location_src_id,
                                    'location_dest_id': location_dest_id,
                                })
                            else:
                                request.env['stock.move'].create({
                                    'product_id': product.id,
                                    'name': product.name,
                                    'product_uom_qty': float(int(v)),
                                    'product_uom': product.uom_id.id,
                                    'location_id': location_src_id,
                                    'location_dest_id': location_dest_id,
                                    'picking_id': picking.id
                                })
                    # remove move lines
                    for line in picking.move_lines:
                        if not post.get('product_qty_%s' %line.product_id.id, False):
                            line.unlink()
                picking.action_confirm() # mark as todo
                picking.action_assign() # check availability
                # do transfer
                if picking.state == 'assigned':
                    operation_completed = []
                    for line in picking.move_lines:
                        try:
                            ops = request.env['stock.pack.operation'].search([('product_id', '=', line.product_id.id), ('picking_id', '=', picking.id), ('location_id', '=', location_src_id), ('location_dest_id', '=', location_dest_id)])
                            if len(ops) > 0:
                                op = ops[0]
                                if len(ops) > 1:
                                    for o in ops:
                                        if o != op:
                                            o.unlink()
                                op.write({
                                    'product_id': line.product_id.id,
                                    'picking_id': picking.id,
                                    'location_id': location_src_id,
                                    'location_dest_id': location_dest_id,
                                    'product_qty': line.product_uom_qty,
                                    'qty_done': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'processed': 'true'
                                })
                            else:
                                request.env['stock.pack.operation'].create({
                                    'product_id': line.product_id.id,
                                    'picking_id': picking.id,
                                    'location_id': location_src_id,
                                    'location_dest_id': location_dest_id,
                                    'product_qty': line.product_uom_qty,
                                    'qty_done': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'processed': 'true'
                                })
                            operation_completed.append(True)
                        except:
                            operation_completed.append(False)
                    if all(operation_completed):
                        picking.do_transfer()
                return request.website.render('stock_quickmove.webapp', {'move_class':'active','picking_type_id': picking.picking_type_id.id, 'previous_picking_id': picking.id, 'title':'Stock Quick Move'})
                # ~ return request.redirect('/stock/quickmove/picking/%s' %picking.id)
        return request.website.render('stock_quickmove.webapp', {'move_class':'active','picking_type_id': post.get('picking_type_id' or ''), 'picking': picking, 'title':'Stock Quick Move'})

    @http.route(['/stock/quickmove_barcode'], type='json', auth='user', website=True)
    def quickmove_barcode(self, barcode='', location_src_scanned=False, **kw):
        # search EAN13
        product_ids = request.env['product.product'].search([('ean13', '=', barcode)])
        if len(product_ids) > 0:
            products = []
            for p in product_ids:
                products = [p.id, p.display_name]
            return {'type': 'product', 'product_ids': products}
        else:
            if not location_src_scanned:
                # search sorce location
                src_location_ids = request.env['stock.location'].search([('name', '=', barcode)])
                if len(src_location_ids) > 0:
                    src_location_id = src_location_ids[0]
                    return {'type': 'src_location', 'location': {'id': src_location_id.id, 'name': src_location_id.display_name}}
            else:
                # search destination location
                dest_location_ids = request.env['stock.location'].search([('name', '=', barcode)])
                if len(dest_location_ids) > 0:
                    dest_location_id = dest_location_ids[0]
                    return {'type': 'dest_location', 'location': {'id': dest_location_id.id, 'name': dest_location_id.display_name}}

    @http.route(['/stock/quickmove_location_search'], type='http', auth='user', website=True)
    def quickmove_location_search(self, **post):
        word = post.get('term')
        results = []
        locations = request.env['stock.location'].search_read([('name', 'ilike', word)], fields=['id', 'display_name'])
        if len(locations) > 0:
            for l in locations:
                results.append({'id': l.get('id'), 'text': l.get('display_name')})
        return Response(simplejson.dumps({'results': results}), mimetype='application/json')

    @http.route(['/stock/quickmove_product_search'], type='http', auth='user', website=True)
    def quickmove_product_search(self, word='', **post):
        word = post.get('term')
        results = []
        products = request.env['product.product'].search_read(['|', '|', ('name', 'ilike', word), ('default_code', 'ilike', word), ('ean13', 'ilike', word)], fields=['id', 'display_name'])
        if len(products) > 0:
            for p in products:
                results.append({'id': p.get('id'), 'text': p.get('display_name')})
        return Response(simplejson.dumps({'results': results}), mimetype='application/json')


    @http.route(['/stock/quickmove_get_product_stock'], type='json', auth='user', website=True)
    def quickmove_get_product_stock(self, location_id=None, product_id=None, **kw):
        product_id = product_id and int(product_id)
        location_id = location_id and int(location_id)
        res = []
        if product_id:
            products = request.env['product.product'].browse(product_id)
        else:
            products = request.env['product.product'].search([('stock_location_id', '=', location_id)])
        for product in products:
            quants = request.env['stock.quant'].search([('product_id', '=', product.id), ('location_id', '=', location_id)])
            reserved_qty = sum(quants.filtered(lambda q: True if q.reservation_id else False).mapped('qty'))
            unreserved_qty = sum(quants.filtered(lambda q: False if q.reservation_id else True).mapped('qty'))
            res.append([product.id, product.display_name, reserved_qty, reserved_qty + unreserved_qty, unreserved_qty])
        return res
        

    @http.route(['/stock/quickmove_location_search_products'], type='json', auth='user', website=True)
    def quickmove_location_search_products(self, location='0', **kw):
        product_ids = request.env['product.product'].search([('stock_location_id', '=', int(location))])
        products = []
        for p in product_ids:
            qty = sum(request.env['stock.quant'].search([('product_id', '=', p.id), ('location_id', '=', int(location))]).mapped('qty'))
            products.append([p.id, '%s %s' %(p.name, ','.join([a.name for a in p.attribute_value_ids])), qty])
        return {'product_ids': products}
    
    # ----- inventory methods ----------------
    @http.route(['/stock/inventory','/stock/inventory/<model("product.product"):product>'], type='http', auth='user', website=True)
    def quickmove_inventory(self, product=None, **post):
        return request.website.render('stock_quickmove.webapp_inventory',{'title':'Inventory','product':product,'inv_class':'active'})
        
    @http.route(['/stock/inventory_search_product_location'], type='json', auth='user', website=True)
    def quickmove_inventory_search_product_location(self, product_id, **kw):
        product_locations = []
        stock_warehouse_ids = request.env['stock.warehouse'].search([])
        # stock_location = request.env.ref('stock.stock_location_stock')
        # ~ quants = request.env['stock.quant'].search([('product_id','=',product_id),('location_id','child_of',stock_location.id)])
        quants = request.env['stock.quant'].search([('product_id','=',int(product_id)),('location_id','child_of',stock_warehouse_ids.mapped('lot_stock_id.id'))])
        for location in quants.mapped('location_id'):
            product_locations.append({
                'qty':sum(quants.filtered(lambda q: q.location_id == location).mapped('qty')),
                'name': location.name,
                'location_id': location.id})
        
        return product_locations # list of dicts
        
    @http.route(['/stock/inventory_adjust'], type='json', auth='user', website=True)
    def quickmove_inventory_adjust(self, location_id, product_id, quantity):
        #
            inventory = request.env['stock.inventory'].create({'name':'test', 'product_id':product_id, 'location_id':location_id, 'filter':'product'})
            inventory.prepare_inventory()
            
            if inventory.line_ids:
                inventory.line_ids[0].product_qty = quantity
                inventory.action_done()
            else:
                raise Warning('No stock for %s on location %s'% (inventory.product_id.display_name,inventory.location_id.display_name))

    @http.route(['/stock/quickmove_get_location'], type='json', auth='user', website=True)
    def quickmove_get_location(self, **kw):
        location = kw.get('location')
        if location:
            location_res = request.env['stock.location'].search_read([('id', '=', location)], fields=['display_name'])
            if location_res:
                location_name = location_res[0]['display_name']
            else:
                location_name = ''
        else:
            location = ''
            location_name = ''

        return {'location_id': location, 
                'location_name': location_name}

    @http.route(['/stock/quickmove_get_product'], type='json', auth='user', website=True)
    def quickmove_get_product(self, **kw):
        product = kw.get('product')
        if product:
            product_res = request.env['product.product'].search_read([('id', '=', product)], fields=['display_name'])
            if product_res:
                product_name = product_res[0]['display_name']
            else:
                product_name = ''
        else:
            product = ''
            product_name = ''
            
        return {'product_id': product, 
                'product_name': product_name}
