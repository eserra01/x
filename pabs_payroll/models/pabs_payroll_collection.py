# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.pabs_payroll.models.pabs_payroll import WEEK, STATES
from odoo.addons.pabs_payroll.models.pabs_payroll_high_investment import VALUES
from datetime import datetime

class PabsPayrollCollection(models.Model):
  _name = 'pabs.payroll.collection'
  _description = 'Nómina Sección de Cobranza'

  name = fields.Char(string='Folio')

  state = fields.Selection(selection=STATES,
    string='Estado',
    default='draft')
  
  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    string='Oficina de Ventas',
    required=True)

  user_id = fields.Many2one(comodel_name='res.users',
    string='Usuario',
    default=lambda self: self.env.user)

  week_number = fields.Selection(selection=WEEK,
    string='Semana',
    required=True,
    default=lambda self: self._calc_week_number())

  first_date = fields.Date(string='Fecha Inicio')

  end_date = fields.Date(string='Fecha Fin')

  salary_ids = fields.One2many(comodel_name='pabs.payroll.salary',
    inverse_name='payroll_id',
    string='Sueldos')

  complement_ids = fields.One2many(comodel_name='pabs.payroll.complements',
    inverse_name = 'payroll_id',
    string='Complementos')

  high_investment_det_ids = fields.One2many(comodel_name='pabs.payroll.high.investment.det',
    inverse_name='payroll_id',
    string='Inversión alta detallada')
  
  def _calc_week_number(self):
    today = datetime.today()
    week_number = (int(today.strftime("%U")) - 1)
    if week_number < 10:
      week_number = str(week_number).zfill(2)
    self.week_number = week_number
    return week_number

  @api.onchange('week_number')
  def calc_dates(self):
    year = fields.Date.today().year
    week_config_obj = self.env['week.number.config']
    year_config_obj = self.env['week.year']
    year_id = year_config_obj.search([
      ('name','=',year)],limit=1)
    if not year_id:
      raise ValidationError((
        "No se ha configurado el año en curso, favor de comunicarse con sistemas"))
    for rec in self:
      if rec.week_number:
        record = week_config_obj.search([
          ('number_week','=',rec.week_number),
          ('year','=',year_id.id)])
        if not record:
          rec.first_date = False
          rec.end_date = False
          return {
            'warning': {
              'title': ("Error en busqueda de Semana"),
              'message': "No se encontró coincidencias para la {}".format(
              dict(rec._fields['week_number'].selection).get(rec.week_number))
            }
          }
        rec.first_date = record.first_date
        rec.end_date = record.end_date

  @api.onchange('warehouse_id','first_date', 'end_date')
  def _calc_all_contracts(self):
    contract_obj = self.env['pabs.contract']
    for rec in self:
      rec.high_investment_det_ids = [(5,0,0)]
      all_records = []
      if rec.warehouse_id and rec.first_date and rec.end_date:
        all_contracts = contract_obj.search([
          ('state','=','contract'),
          ('invoice_date','>=',rec.first_date),
          ('invoice_date','<=',rec.end_date)],order="employee_id")
        for contract_id in all_contracts:
          if rec.warehouse_id.id == contract_id.employee_id.warehouse_id.id:
            initial = contract_id.initial_investment
            bonus = 0
            if initial >= 500 and initial < 1000:
              bonus = VALUES['500']
            elif initial >= 1000:
              bonus = VALUES['1000']
            all_records.append([0,0,{
              'contract_id' : contract_id.id,
              'employee_id' : contract_id.employee_id.id,
              'contract_date' : contract_id.invoice_date,
              'high_investment' : initial,
              'high_investment_bonus' : bonus,
            }])
      if all_records:
        rec.high_investment_det_ids = all_records
