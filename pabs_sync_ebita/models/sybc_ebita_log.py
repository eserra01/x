# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api

class SyncEbitaLog(models.Model):
  _name = 'sync.ebita.log'
  _description = 'Log sincroniación Ebita'
  _order = 'create_date desc'
  
  description = fields.Text(string="Descripción")  
  company_id = fields.Many2one(comodel_name='res.company', string=u'Compañía', readonly=True, default=lambda self: self.env.company)