# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Resusers(models.Model):
    _inherit = 'res.users'

    all_employees = fields.Boolean(string="Ver todos los empleados")