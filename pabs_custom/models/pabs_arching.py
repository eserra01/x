# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

STATES = [
  ('draft','Borrador'),
  ('done','Hecho')]

class SaleOrder(models.Model):
  _name = 'pabs.arching'

  state = fields.Selection(selection=STATES,
    string='Estado',
    default='draft')

  name = fields.Char(string='Folio',
    default='Nuevo')

  code = fields.Char(string='Código de asociado',
    required=True)

  employee_id = fields.Many2one(comodel_name='hr.employee',
    compute='_calc_employee_values',
    string='Nombre de asociado')

  office_code = fields.Char(string='Código de oficina',
    compute='_calc_employee_values')

  office_id = fields.Many2one(comodel_name='pabs.office',
    compute='_calc_employee_values',
    string='Nombre de oficina')

  line_ids = fields.One2many(comodel_name='pabs.arching.line',
    inverse_name='arching_id',
    string='Solicitudes')

  @api.onchange('code')
  def _calc_employee_values(self):
    for obj in self:
      if not obj.code:
        obj.employee_id = False
        obj.office_code = False
        obj.office_id = False
      else:
        obj.code = obj.code.upper()
        employee_id = obj.env['hr.employee'].search([('barcode','=',obj.code)])
        obj.employee_id = employee_id.id
        obj.office_code = employee_id.office_id.code
        obj.office_id = employee_id.office_id.id

  def close_arching(self):
    if not self.employee_id or not self.office_code or not self.office_id:
      raise ValidationError(
        ('No puedes cerrar un arqueo porque no se encontró ninguna información del asociado'))
    if len(self.line_ids) < 1:
      raise ValidationError(
        ('No puedes cerrar un arqueo porque no se ha capturado ninguna solicitud'))
    self.state = 'done'
    self.name = self.env['ir.sequence'].next_by_code(
      'pabs.arching') or 'Nuevo'
