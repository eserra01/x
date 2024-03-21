# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockLocation(models.Model):
    _inherit = 'stock.location'

    pabs_stock_location = fields.Boolean(string="Manejo de almacén PABS")
