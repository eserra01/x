# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
  _inherit = 'res.company'

  bonus_as = fields.Boolean(string="Aplica bono de AS")

  def reset_passwords(self,company_id):
    # Se obtienen los usuarios activos de la compañía
    user_ids = self.env['res.users'].search(
    [
      ('company_id','=',company_id),
      ('active','=',True),
      ('exclude_pass_reset','=',False)
    ])
    
    # Se intenta el reseteo del password
    for user in user_ids:
      if user.login != 'admin':        
        try:
          user.password = False
          user.action_reset_password()
        except:       
          user.password = False     
    return True
  