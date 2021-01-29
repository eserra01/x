# -*- coding: utf-8 -*-
# from odoo import http


# class Mortuary(http.Controller):
#     @http.route('/mortuary/mortuary/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mortuary/mortuary/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mortuary.listing', {
#             'root': '/mortuary/mortuary',
#             'objects': http.request.env['mortuary.mortuary'].search([]),
#         })

#     @http.route('/mortuary/mortuary/objects/<model("mortuary.mortuary"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mortuary.object', {
#             'object': obj
#         })
