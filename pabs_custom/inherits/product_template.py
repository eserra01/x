# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
  _inherit = 'product.template'

  contract_xml_id = fields.Char(string='xml id del contrato', help="Aqui se asigna el xml id del formato del contrato (DOCX)")