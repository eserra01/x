# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class BonusPabs(models.Model):
  _name = 'pabs.bonus'

  plan_id = fields.Many2one(comodel_name = 'product.product',
    required=True,
    string='Plan')

  min_value = fields.Float(string='Valor minimo',
    required=True)

  max_value = fields.Float(string='Valor Maximo',
    required=True)

  bonus = fields.Float(string='Valor asignado',
    required=True)

  @api.model
  def create(self, vals):
    min_value = vals.get('min_value')
    max_value = vals.get('max_value')
    if max_value < min_value:
      raise ValidationError((
        "{} es menor que {} favor de verificar la información".format(max_value, min_value)))
    return super(BonusPabs, self).create(vals)
    