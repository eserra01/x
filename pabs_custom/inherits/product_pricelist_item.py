# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ProductPricelistItem(models.Model):
  _inherit = 'product.pricelist.item'

  ### Declaración de campos
  prefix_contract = fields.Char(string='Prefijo contratos', required=True)

  prefix_request = fields.Char(string='Prefijo solicitudes', required=True)

  stationery = fields.Float(string='Papelería', required=True)

  min_quantity = fields.Integer(default=1)

  sequence_id = fields.Many2one(comodel_name='ir.sequence', string='Secuencia')

  type_company = fields.Many2one(comodel_name='type.company', string='Empresa', required=True)

  payment_amount = fields.Float(string="Pago semanal")

  @api.onchange('type_company','prefix_request')
  def validate_code(self):
    for rec in self:
      if rec.prefix_request:
        if rec.type_company:
          if rec.type_company.code != rec.prefix_request[2:4]:
            raise ValidationError((
              "El código de {} debe de ser {}".format(rec.type_company.name, rec.type_company.code)))

  sequence_id = fields.Many2one(comodel_name='ir.sequence', string='Secuencia')

  type_company = fields.Many2one(comodel_name='type.company', string='Empresa', required=True)

  payment_amount = fields.Float(string="Pago semanal")

  @api.onchange('type_company','prefix_request')
  def validate_code(self):
    for rec in self:
      if rec.prefix_request:
        if rec.type_company:
          if rec.type_company.code != rec.prefix_request[2:4]:
            raise ValidationError((
              "El código de {} debe de ser {}".format(rec.type_company.name, rec.type_company.code)))

  @api.onchange('product_tmpl_id')
  def onchange_product_tmpl(self):
    product_obj = self.env['product.product']
    if self.product_tmpl_id:
      product = product_obj.search([
        ('product_tmpl_id','=',self.product_tmpl_id.id)],limit=1)
      if product:
        self.product_id = product.id

  @api.model
  def create(self, vals):
    sequence_obj = self.env['ir.sequence']
    if vals.get('prefix_contract'):
      data = {
        'name' : vals.get('prefix_request'),
        'code' : 'pabs.{}'.format(vals.get('prefix_contract')),
        'implementation' : 'standard',
        'prefix' : vals.get('prefix_contract'),
        'padding' : 6,
        'number_increment' : 1,
        'number_next' : 1,
        'number_next_actual' : 1,
      }
      sequence_id = sequence_obj.create(data)
      if sequence_id: 
        vals['sequence_id'] = sequence_id.id

    return super(ProductPricelistItem, self).create(vals)
