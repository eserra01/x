# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.pabs_payroll.models.pabs_payroll import WEEK, STATES
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

  complement_ids = fields.One2many(comodel_name='pabs.payroll.complements',
    inverse_name = 'payroll_id',
    string='Complementos')

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
            'payroll_collection_id' : self.id,
          })
        registry_obj.create(rec_data)
    else:
      registry_ids.payroll_collection_id = self.id
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
    return super(PabsPayrollCollection, self).create(vals)

  _sql_constraints = [
    ('unique_warehouse_on_week',
      'UNIQUE(week_number, warehouse_id)',
      'No se puede crear el registro: solo puede existir un registro por Semana'),
    ]