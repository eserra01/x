# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'    

    pabs_eleanor_area_id = fields.Many2one(comodel_name="pabs.eleanor.area", string="Área")
