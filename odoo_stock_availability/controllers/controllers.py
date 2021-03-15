# -*- coding: utf-8 -*-
# from odoo import http


# class Odoo-stock-availability(http.Controller):
#     @http.route('/odoo-stock-availability/odoo-stock-availability/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo-stock-availability/odoo-stock-availability/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo-stock-availability.listing', {
#             'root': '/odoo-stock-availability/odoo-stock-availability',
#             'objects': http.request.env['odoo-stock-availability.odoo-stock-availability'].search([]),
#         })

#     @http.route('/odoo-stock-availability/odoo-stock-availability/objects/<model("odoo-stock-availability.odoo-stock-availability"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo-stock-availability.object', {
#             'object': obj
#         })
