# -*- coding: utf-8 -*-
# from odoo import http


# class Colonias(http.Controller):
#     @http.route('/colonias/colonias/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/colonias/colonias/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('colonias.listing', {
#             'root': '/colonias/colonias',
#             'objects': http.request.env['colonias.colonias'].search([]),
#         })

#     @http.route('/colonias/colonias/objects/<model("colonias.colonias"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('colonias.object', {
#             'object': obj
#         })
