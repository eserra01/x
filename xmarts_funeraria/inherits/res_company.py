# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResCompany(models.Model):
  _inherit = 'res.company'

  service_phone = fields.Char(string='Telefono de servicio')
  