# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class PabsChangesFormatApprove(models.Model):
  _name = 'pabs.changes.format.approver'  
  _description = 'Aprobadores'  

  name = fields.Char(string="Nombre", required=True )    
  password = fields.Char(string="Contraseña", required=True)
  office_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string="Oficinas permitidas",
        relation='approver_warehouse_rel',
        column1='approver_id',
        column2='warehouse_id',
        domain="[('lot_stock_id.office_location','=',True)]"
    )
  operation_ids = fields.Many2many(
        comodel_name='pabs.changes.format.operation',
        string="Operaciones permitidas",
        relation='approver_operation_rel',
        column1='approver_id',
        column2='operation_id'
    )
  company_id = fields.Many2one(comodel_name='res.company', string='Compañia', required=True, default=lambda s: s.env.company.id,tracking=True)

  