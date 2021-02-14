# -*- coding: utf-8 -*-

from odoo import api, fields, models

CITIES = [
  ('ecobroSAP_ACA','Acapulco')]

class ResConfigSettings(models.TransientModel):
  _inherit = 'res.config.settings'

  ecobro_ip = fields.Char(string='IP WebService')

  testing_ecobro = fields.Boolean(string='WebService de pruebas')

  ecobro_city = fields.Selection(selection=CITIES)

  def set_values(self):
    super(ResConfigSettings, self).set_values()
    param_obj = self.env['ir.config_parameter']
    param_obj.set_param('testing_ecobro',self.testing_ecobro)
    if self.testing_ecobro:
      ip = '35.167.149.196'
      param_obj.set_param('ecobro_ip',ip)
      param_obj.set_param('ecobro_city',"")
    else:
      param_obj.set_param('ecobro_ip',self.ecobro_ip)
      param_obj.set_param('ecobro_city',self.ecobro_city)

  def get_values(self):
    param_obj = self.env['ir.config_parameter']
    res = super(ResConfigSettings, self).get_values()
    res.update({
      'testing_ecobro' : param_obj.get_param('testing_ecobro'),
      'ecobro_city' : param_obj.get_param('ecobro_city'),
      'ecobro_ip': param_obj.get_param('ecobro_ip')})
    return res
    