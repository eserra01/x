# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.addons.pabs_payroll.models.pabs_payroll import WEEK

class GenerateYearsWizard(models.TransientModel):
  _name = 'pabs.payroll.generate.year.wizard'

  name = fields.Char(string='Escribe el año que deseas generar',
    required=True)

  first_day = fields.Date(string='Primer día de la semana',
    required=True)
  
  def generate_fiscal_year(self):
    year_obj = self.env['week.year']
    week_obj = self.env['week.number.config']
    if self.name:
      first_day = self.first_day
      year_prev = year_obj.search([
        ('name','=',self.name)])
      if year_prev:
        raise ValidationError((
          "El año {} ya fue generado previamente.".format(self.name)))
      year_id = year_obj.create({
        'name' : self.name})
      first_date = first_day
      for week in WEEK:
        end_date = first_date + timedelta(days=6)
        week_obj.create({
          'year' : year_id.id,
          'number_week' : week[0],
          'first_date' : first_date,
          'end_date' : end_date,
        })
        first_date = end_date + timedelta(days=1)
        