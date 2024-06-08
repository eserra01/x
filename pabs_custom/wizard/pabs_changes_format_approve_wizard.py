# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError



class PabsChangesFormatApproveWizard(models.TransientModel):
  _name = 'pabs.changes.format.approve.wizard'
  _description = 'Aprobar solicitud de cambios'

  password = fields.Char(string="Cotraseña",)
  info = fields.Char(string="Información",readonly=True,default='')
  format_id = fields.Many2one(comodel_name='pabs.changes.format', string="Solicitud")

  def approve_action(self):
    #
    if self.password == self.format_id.approver_id.password:
      self.format_id.approve_action()
      return True
    else:
      self.info = "Contraseña incorrecta"
      return {        
              'name': "Especificar contraseña para aprobar solicitud",
              # 'context': {'show_info': False},    
              'view_type': 'form',        
              'view_mode': 'form',        
              'res_model': 'pabs.changes.format.approve.wizard', 
              'res_id': self.id,
              'views': [(False, 'form')],            
              'type': 'ir.actions.act_window',        
              'target': 'new',    
          }   
   
   

 