# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class UpdateAddressLog(models.Model):
  _name = 'update.address.log'
  _rec_name = 'create_date'
  _order = 'create_date desc'

  registers = fields.Integer(string="Total de registros")
  updates = fields.Integer(string="Registros actualizados")
  errors = fields.Integer(string="Registros con error")
  line_ids = fields.One2many(comodel_name="update.address.log.line", inverse_name="log_id",string="Líneas de log")
  company_id = fields.Many2one('res.company', 'Compañia', required=True,  default=lambda s: s.env.company.id, index=True)

  def action_detail(self):   
    return {
        'name':'Detalle de log',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'update.address.log',
        'type': 'ir.actions.act_window',
        'nodestroy': True,
        'target': 'new',
        'res_id': self.id,
    }  

class UpdateAddressLogLine(models.Model):
  _name = 'update.address.log.line'

  log = fields.Char(string="Log")
  log_id = fields.Many2one(comodel_name='update.address.log')
  idRegistro = fields.Char(string="IDRegistro")
  contract = fields.Char(string="Contrato")
  company_id = fields.Many2one('res.company', 'Compañia', required=True,  default=lambda s: s.env.company.id, index=True)

