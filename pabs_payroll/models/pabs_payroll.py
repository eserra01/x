# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.pabs_payroll.models.pabs_payroll_high_investment import VALUES
from datetime import datetime, timedelta
import xml.etree.ElementTree as etree

STATES = [
  ('draft','Borrador'),
  ('to review','En revisión'),
  ('done','Finalizado')
]

WEEK = [
  ('01', 'Semana 1'),('02', 'Semana 2'),('03', 'Semana 3'),('04', 'Semana 4'),
  ('05', 'Semana 5'),('06', 'Semana 6'),('07', 'Semana 7'),('08', 'Semana 8'),
  ('09', 'Semana 9'),('10', 'Semana 10'),('11', 'Semana 11'),('12', 'Semana 12'),
  ('13', 'Semana 13'),('14', 'Semana 14'),('15', 'Semana 15'),('16', 'Semana 16'),
  ('17', 'Semana 17'),('18', 'Semana 18'),('19', 'Semana 19'),('20', 'Semana 20'),
  ('21', 'Semana 21'),('22', 'Semana 22'),('23', 'Semana 23'),('24', 'Semana 24'),
  ('25', 'Semana 25'),('26', 'Semana 26'),('27', 'Semana 27'),('28', 'Semana 28'),
  ('29', 'Semana 29'),('30', 'Semana 30'),('31', 'Semana 31'),('32', 'Semana 32'),
  ('33', 'Semana 33'),('34', 'Semana 34'),('35', 'Semana 35'),('36', 'Semana 36'),
  ('37', 'Semana 37'),('38', 'Semana 38'),('39', 'Semana 39'),('40', 'Semana 40'),
  ('41', 'Semana 41'),('42', 'Semana 42'),('43', 'Semana 43'),('44', 'Semana 44'),
  ('45', 'Semana 45'),('46', 'Semana 46'),('47', 'Semana 47'),('48', 'Semana 48'),
  ('49', 'Semana 49'),('50', 'Semana 50'),('51', 'Semana 51'),('52', 'Semana 52')
]

class PabsPayroll(models.Model):
  _name = 'pabs.payroll'
  _description = 'Incidencias de Nómina'

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

  support_ids = fields.One2many(comodel_name='pabs.payroll.support',
    inverse_name='payroll_id',
    string='Apoyos')

  high_investment_ids = fields.One2many(comodel_name='pabs.payroll.high.investment',
    inverse_name='payroll_id',
    string='Inversión Alta')

  support_total = fields.Float(string='Total Apoyo', readonly=True,
        compute='_calc_support',
        inverse='_inverse_support_total')

  # high_investment_total = fields.Float(string='Total Inversión Alta', store=True, readonly=True,
  #   compute="_calc_high_investment_total",
  #   inverse="_inverse_investment_total")

  @api.depends(
    'support_ids.productivity_bonus',
    'support_ids.five_hundred_support',
    'support_ids.permanence_bonus')
  def _calc_support(self):
    for rec in self:
      productivity_total = sum(rec.support_ids.mapped('productivity_bonus'))
      five_hundred_total = sum(rec.support_ids.mapped('five_hundred_support'))
      permanence_total = sum(rec.support_ids.mapped('permanence_bonus'))
      total = productivity_total + five_hundred_total + permanence_total
      rec.support_total = total
  
  def _calc_week_number(self):
    today = datetime.today()
    week_number = (int(today.strftime("%U")) - 1)
    if week_number < 10:
      week_number = str(week_number).zfill(2)
    else:
      week_number = str(week_number)
    self.week_number = week_number
    return week_number

  @api.onchange('week_number')
  def calc_dates(self):
    registry_obj = self.env['pabs.payroll.registry']
    res = {}
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
    ### IDS DE LOS ALMACENES
    warehouse_ids = registry_obj._get_warehouse_ids()
    res['domain'] = {'warehouse_id': [('id', 'in', tuple(warehouse_ids) )], } 
    return res

  def validate(self):
    ### CREAR OBJETO DE REGISTRO
    registry_obj = self.env['pabs.payroll.registry']
    registry_ids = registry_obj.search([
      ('warehouse_id','=',self.warehouse_id.id),
      ('week_number','=',self.week_number)])
    if not registry_ids:
      warehouse_ids = registry_obj._get_warehouse_ids()
      for warehouse_id in warehouse_ids:
        rec_data = {
          'warehouse_id' : warehouse_id,
          'week_number' : self.week_number,
        }
        if warehouse_id == self.warehouse_id.id:
          rec_data.update({
            'payroll_id' : self.id,
          })
        registry_obj.create(rec_data)
    else:
      registry_ids.payroll_id = self.id
    self.state = 'to review'
    self.name = 'Nómina {} {}'.format(
      self.warehouse_id.name, 
      dict(self._fields['week_number'].selection).get(self.week_number))


  @api.model
  def create(self, vals):
    week_config_obj = self.env['week.number.config']
    year_config_obj = self.env['week.year']
    year = fields.Date.today().year
    year_id = year_config_obj.search([
      ('name','=',year)],limit=1)
    record = week_config_obj.search([
      ('number_week','=',vals['week_number']),
      ('year','=',year_id.id)])
    vals['first_date'] = record.first_date
    vals['end_date'] = record.end_date
    return super(PabsPayroll, self).create(vals)

  @api.onchange('warehouse_id','first_date', 'end_date')
  def _calc_high_investment(self):
    self.high_investment_ids = [(5,0,0)]
    contract_obj = self.env['pabs.contract']
    initial_investment = []
    supports = []
    ### SE SUMAN 12 SEMANAS (3 MESES)
    limit_days = timedelta(weeks=12)
    if self.warehouse_id and self.first_date and self.end_date:
      payment_scheme = self.env['pabs.payment.scheme'].search([
        ('name','=','COMISION')])
      all_contracts = contract_obj.search([
        ('state','=','contract'),
        ('invoice_date','>=',self.first_date),
        ('invoice_date','<=',self.end_date)],)
      employee_ids = all_contracts.mapped('employee_id')
      for employee_id in employee_ids:
        if self.warehouse_id.id == employee_id.warehouse_id.id:
          five_hundred = 0
          one_thousand = 0
          sup = 0
          contract_ids = all_contracts.filtered(lambda x : x.employee_id.id == employee_id.id)
          for contract_id in contract_ids:
            if contract_id.initial_investment >= 500 and contract_id.initial_investment < 1000:
              five_hundred += 1
            elif contract_id.initial_investment >= 1000:
              one_thousand += 1
            ### APOYOS
            if employee_id.payment_scheme.id == payment_scheme.id:
              limit_date = employee_id.date_of_admission + limit_days
              if contract_id.invoice_date <= limit_date:
                sup += 1

          if five_hundred or one_thousand:
            initial_investment.append([0,0,{
              'employee_id' : employee_id.id,
              'five_hundred_investment' : five_hundred,
              'one_thousand_investment' : one_thousand,
              'five_hundred_bonus' : float(five_hundred * VALUES['500']),
              'one_thousand_bonus' : float(one_thousand * VALUES['1000']),
            }])
          ### VALIDAMOS LA CANTIDAD DE APOYOS
          if sup == 1:
            supports.append([0,0,{
              'employee_id' : employee_id.id,
              'five_hundred_support' : 250,
            }])
          elif sup >= 2:
            supports.append([0,0,{
              'employee_id' : employee_id.id,
              'five_hundred_support' : 500,
            }])
    if initial_investment:
      self.high_investment_ids = initial_investment
    if supports:
      self.support_ids = supports

  _sql_constraints = [
    ('unique_warehouse_on_week',
      'UNIQUE(week_number, warehouse_id)',
      'No se puede crear el registro: solo puede existir un registro de esa oficina de ventas por Semana'),
    ]
    