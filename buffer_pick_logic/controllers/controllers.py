# -*- coding: utf-8 -*-
# from odoo import http


# class BufferPickLogicDermanord(http.Controller):
#     @http.route('/buffer_pick_logic_dermanord/buffer_pick_logic_dermanord/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/buffer_pick_logic_dermanord/buffer_pick_logic_dermanord/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('buffer_pick_logic_dermanord.listing', {
#             'root': '/buffer_pick_logic_dermanord/buffer_pick_logic_dermanord',
#             'objects': http.request.env['buffer_pick_logic_dermanord.buffer_pick_logic_dermanord'].search([]),
#         })

#     @http.route('/buffer_pick_logic_dermanord/buffer_pick_logic_dermanord/objects/<model("buffer_pick_logic_dermanord.buffer_pick_logic_dermanord"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('buffer_pick_logic_dermanord.object', {
#             'object': obj
#         })
