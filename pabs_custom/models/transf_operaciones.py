# -*- coding: utf-8 -*-

from odoo import fields, models, api

class Operaciones(models.Model):
  _name = 'transf.operaciones'

  name = fields.Char(string="Nombre de transferencia")

  id_user = fields.Many2one(
    'res.users',
    string="Usuario")

  id_producto = fields.Many2one('product.product', string="Producto")
  serie_start = fields.Char(string="Serie inicio")
  demanda = fields.Float(string="Demanda")
  type_transfer = fields.Selection([
    ('sucursal', 'Sucursal'),
    ('asistente', 'Asistente'),
    ('ventas', 'Ventas'),
    ('regreso_solicitudes', 'Regreso de solicitudes')],
    string='Tipo de transferencia')
  