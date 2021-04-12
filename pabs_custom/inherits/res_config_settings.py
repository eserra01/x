# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
  _inherit = 'res.config.settings'

  actually_day = fields.Boolean(string='Día Actual',
    config_parameter='pabs_custom.actually_day')

  last_day = fields.Date(string='Fecha de Corte')

  def set_values(self):
    params_obj = self.env['ir.config_parameter'].sudo()
    res = super(ResConfigSettings, self).set_values()
    params_obj.set_param('pabs_custom.last_day', self.last_day)
    return res 

  @api.model
  def get_values(self):
    res = super(ResConfigSettings, self).get_values()
    params = self.env['ir.config_parameter'].sudo()
    last_day = params.get_param('pabs_custom.last_day')
    res.update({'last_day' : last_day})
    return res

  @api.onchange('actually_day')
  def onchange_actually_day(self):
    if not self.actually_day:
      self.last_day = False