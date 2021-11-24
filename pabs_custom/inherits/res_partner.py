# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
  _inherit = 'res.partner'

  company_id = fields.Many2one(
    'res.company', 'Compañia', index=True)

  def update_accounts(self, company_id=False):   
    #   
    if company_id:
      # Se busca la compañia especificada          
      company = self.env['res.company'].browse(company_id)
      # Se actualiza la compañia en el enviroment
      self.env.company = company      
      # Buscar cuentas contables
      cuenta_a_cobrar = self.env['account.account'].search([('code','=','110.01.001'),('company_id','=',company_id)], limit=1) #Afiliaciones plan previsión
      cuenta_a_pagar = self.env['account.account'].search([('code','=','201.01.001'),('company_id','=',company_id)], limit=1) #Proveedores nacionales      
      if cuenta_a_cobrar and cuenta_a_pagar:       
        partner_ids = self.env['res.partner'].search(['|',('property_account_receivable_id','=',False),('property_account_payable_id','=',False),('company_id','=',company_id)])              
        for partner in partner_ids:                         
          partner.write({'property_account_receivable_id': cuenta_a_cobrar.id, 'property_account_payable_id': cuenta_a_pagar.id})       
    return True