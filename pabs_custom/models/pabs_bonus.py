# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class BonusPabs(models.Model):
  _name = 'pabs.bonus'

  plan_id = fields.Many2one(comodel_name = 'product.product',
    required=True,
    string='Plan')

  min_value = fields.Float(string='Valor minimo',
    required=True)

  max_value = fields.Float(string='Valor Maximo',
    required=True)

  bonus = fields.Float(string='Valor asignado',
    required=True)

  company_id = fields.Many2one(
    'res.company', 'Compañia', required=True,
    default=lambda s: s.env.company.id, index=True)

  @api.model
  def create(self, vals):
    min_value = vals.get('min_value')
    max_value = vals.get('max_value')
    if max_value < min_value:
      raise ValidationError((
        "{} es menor que {} favor de verificar la información".format(max_value, min_value)))
    
    self.env['pabs.bonus.log'].create({
      'bonus_type': 'inv',
      'action': 'create',
      'plan_id': vals['plan_id'],
      'min_value': vals['min_value'],
      'max_value': vals['max_value'],
      'bonus': vals['bonus'],
      'company_id': self.env.company.id
    })

    return super(BonusPabs, self).create(vals)

  def unlink(self):
    for rec in self:
      self.env['pabs.bonus.log'].create({
        'bonus_type': 'inv',
        'action': 'delete',
        'plan_id': rec.plan_id.id,
        'min_value': rec.min_value,
        'max_value': rec.max_value,
        'bonus': rec.bonus,
        'company_id': rec.company_id.id
      })

    return super(BonusPabs, self).unlink()
  
  def write(self, vals):
    self.env['pabs.bonus.log'].create({
      'bonus_type': 'inv',
      'action': 'edit_old',
      'plan_id': self.plan_id.id,
      'min_value': self.min_value,
      'max_value': self.max_value,
      'bonus': self.bonus,
      'company_id': self.company_id.id
    })

    log_dict = {
      'bonus_type': 'inv',
      'action': 'edit_new',
      'company_id': self.env.company.id
    }

    if 'plan_id' in vals.keys():
      log_dict.update({'plan_id': vals['plan_id']})
    elif self.plan_id:
      log_dict.update({'plan_id': self.plan_id.id})
    else:
      log_dict.update({'plan_id': None})

    if 'min_value' in vals.keys():
      log_dict.update({'min_value': vals['min_value']})
    else:
      log_dict.update({'min_value': self.min_value})

    if 'max_value' in vals.keys():
      log_dict.update({'max_value': vals['max_value']})
    else:
      log_dict.update({'max_value': self.max_value})
    
    if 'bonus' in vals.keys():
      log_dict.update({'bonus': vals['bonus']})
    else:
      log_dict.update({'bonus': self.bonus})

    self.env['pabs.bonus.log'].create(log_dict)

    return super(BonusPabs, self).write(vals)

class BonusPabsLog(models.Model):
  _name = 'pabs.bonus.log'
  _description = "Cambios en bonos PABS"

  bonus_type = fields.Selection(string="Tipo de bono", selection=[('inv','Por inversion'), ('as','De asistente')], required=True)
  action = fields.Selection(string="Accion", selection=[('create','Creacion'), ('edit_old','Antes'), ('edit_new','Despues'), ('delete','Eliminacion')], required=True)
  
  plan_id = fields.Many2one(string='Plan', comodel_name='product.product')
  min_value = fields.Float(string='Valor minimo')
  max_value = fields.Float(string='Valor Maximo')
  bonus = fields.Float(string='Valor asignado')
  company_id = fields.Many2one(string='Compañia', comodel_name='res.company')