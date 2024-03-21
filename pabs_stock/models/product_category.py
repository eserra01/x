# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class ProductCategory(models.Model):
    _inherit = 'product.category'

    consumble_account_stock_id = fields.Many2one(string="Cuenta inventario consumibles", comodel_name='account.account', company_dependent=True)
