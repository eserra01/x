from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.pabs_payroll.models.pabs_payroll import WEEK

class WeekNumberConfig(models.Model):
  _name = 'week.number.config'

  year = fields.Many2one(comodel_name='week.year',
    string='Año',
    required=True)

  number_week = fields.Selection(selection=WEEK,
    required=True,
    string='Número de Semana')

  first_date = fields.Date(string='Inicio de Semana')

  end_date = fields.Date(string='Fin de la semana')
