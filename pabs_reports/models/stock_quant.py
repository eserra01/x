# -*- coding: utf-8 -*-

from odoo import api, models, fields

class StockQuant(models.Model):
  _inherit = 'stock.quant'

  initial_investment = fields.Float(string='Inversión inicial',
    compute="_calc_initial_investment")

  def _calc_initial_investment(self):
    ### INSTANCIACIÓN DE OBJETOS
    move_obj = self.env['stock.move']
    ### ARRAY DE VALORES
    res = {}
    for rec in self:
      ### BUSCAMOS EL NÚMERO DE SERIE
      lot_name = rec.lot_id.name
      ### BUSCAMOS EL STOCK MOVE DONDE EXISTA EL NÚMERO DE SERIE
      move_ids = move_obj.search([
        ('series','=',lot_name),
        ('inversion_inicial','>',0),
        ('state','=','done')]).sorted(key=lambda r: r.date)
      if move_ids:
        rec.initial_investment = move_ids[-1].inversion_inicial
      else:
        rec.initial_investment = 0
