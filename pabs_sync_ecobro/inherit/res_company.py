# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResCompany(models.Model):
  _inherit = 'res.company'

  ecobro_ip = fields.Char(string='IP WebService')

  extension_path = fields.Char(string='Path de Conexión')

  