# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime

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
    string='Oficina de Ventas')

  user_id = fields.Many2one(comodel_name='res.users',
    string='Usuario',
    default=lambda self: self.env.user)

  week_number = fields.Selection(selection=WEEK,
    string='Semana',
    default=lambda self: self._calc_week_number())

  first_date = fields.Date(string='Fecha Inicio')

  end_date = fields.Date(string='Fecha Fin')

  support_ids = fields.One2many(comodel_name='pabs.payroll.support',
    inverse_name='payroll_id',
    string='Apoyos')

  referral_id = fields.One2many(comodel_name='pabs.referral.bonuses',
    inverse_name='payroll_id',
    string='Bonos por recomendación')

  reaffiliation_ids = fields.One2many(comodel_name='pabs.payroll.reaffiliations',
    inverse_name='payroll_id',
    string='Reafiliaciones')

  changes_ids = fields.One2many(comodel_name='pabs.funeral.changes',
    inverse_name='payroll_id',
    string='Cambios de funeraria')

  note_ids = fields.One2many(comodel_name='pabs.payroll.notes',
    inverse_name='payroll_id',
    string='Notas')
  
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

  def validate(self):
    sequence_obj = self.env['ir.sequence']
    self.name = sequence_obj.next_by_code('pabs.payroll')
    self.state = 'to review'