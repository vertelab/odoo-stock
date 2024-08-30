import requests
import json

from odoo import http
from odoo.http import Response, request
import logging
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)


class OngoingController(http.Controller):

    @http.route(['/ongoing/incoming'], type='json', auth='public')
    def ongoing_incoming_status(self, **kw):
        data = json.loads(request.httprequest.data)
        _logger.info(f"Ongoing Message Received: {data}")

        stock_picking = request.env['stock.picking'].sudo().search([
            '|',
            ('name', '=', data.get('purchaseOrderNumber')),
            ('ongoing_order_id', '=', data.get('purchaseOrderId'))
        ], limit=1)

        if not stock_picking:
            return Response(status=404)

        picking_vals = {
            'ongoing_order_status': data.get('purchaseOrderStatus', {}).get('number'),
        }
        if not stock_picking.ongoing_order_id:
            picking_vals['ongoing_order_id'] = data.get('purchaseOrderId')

        stock_picking.write(picking_vals)

    @http.route(['/ongoing/outgoing'], type='json', auth='public')
    def ongoing_outgoing_status(self, **kw):
        data = json.loads(request.httprequest.data)
        _logger.info(f"Ongoing Message Received: {data}")

        stock_picking = request.env['stock.picking'].sudo().search([
            '|',
            ('name', '=', data.get('orderNumber')),
            ('ongoing_order_id', '=', data.get('orderId'))
        ], limit=1)

        if not stock_picking:
            return Response(status=404)

        picking_vals = {
            'ongoing_order_status': data.get('orderStatus', {}).get('number'),
        }
        if not stock_picking.ongoing_order_id:
            picking_vals['ongoing_order_id'] = data.get('orderId')

        stock_picking.write(picking_vals)

    @http.route(['/ongoing/article'], type='json', auth='public')
    def ongoing_article_status(self, **kw):
        data = json.loads(request.httprequest.data)
        _logger.info(f"Ongoing Message Received: {data}")

        product_id = request.env['product.product'].sudo().search([
            '|',
            ('ongoing_article_number', '=', data.get('articleNumber')),
            ('ongoing_article_id', '=', data.get('articleSystemId'))
        ], limit=1)

        if not product_id:
            return Response(status=404)

        product_vals = {}
        if not product_id.ongoing_article_id:
            product_vals['ongoing_article_id'] = data.get('articleSystemId')

        product_id.write(product_vals)

