# -*- coding: utf-8 -*-

from odoo import fields, models, api

class DetOperaciones(models.Model):
  _name = 'det.operaciones'

  transf_operaciones = fields.Many2one(
    'transf.operaciones',
    string="Nombre de transferencia")

  serie = fields.Char(string="Serie")
  