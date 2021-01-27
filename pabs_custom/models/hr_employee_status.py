# -*- coding: utf-8 -*-

from odoo import fields, models, api

class HREmployeeStatus(models.Model):
  _name = 'hr.employee.status'

  name = fields.Char(string='Nombre del estatus',
    required=True)
