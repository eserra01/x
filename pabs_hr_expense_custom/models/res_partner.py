from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
  _inherit = 'res.partner'

  is_supplier = fields.Boolean(string="¿Es proveedor para gastos?", default=False)