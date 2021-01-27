from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PabsReferralBonus(models.Model):
  _name = 'pabs.referral.bonuses'
  _description = 'Bonificaciones por recomendación en nóminas'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina')
  
  employee_rec_id = fields.Many2one(comodel_name='hr.employee',
    string='Recomienda',
    required=True)

  employe_id = fields.Many2one(comodel_name='hr.employee',
    string='Recomendado',
    required=True)

  bonus = fields.Float(string='Bono',
    required=True)
  