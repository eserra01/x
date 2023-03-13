# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEleanorPeriod(models.Model):
    _name = 'pabs.eleanor.period'
    _description = 'Periodos'    
    _rec_name = 'week_number'

    week_number = fields.Integer(string="Número de periodo", required=True)
    date_start = fields.Date(string="Fecha inicio", required=True)
    date_end = fields.Date(string="Fecha fin", required=True)
    period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo", required=True)
    state = fields.Selection([('open','Abierto'),('close','Cerrado')], string="Estatus", required=True, default='open')
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,)

    @api.constrains('state')
    def _check_order(self):       
        for record in self:  
            period_id = self.search([
                ('period_type','=',record.period_type),
                ('state','=','open'),
                ('company_id','=',self.env.company.id)
            ])
                    
            if len(period_id) > 1:
                raise ValidationError("Ya existe un periodo abierto con el tipo seleccionado, por favor cierre el periodo para poder crear uno nuevo.") 

    def close_period(self):
        vals = {'info': 'Esta acción cerrará el periodo seleccionado, de click en Aceptar para continuar...'}
        wizard_id = self.env['pabs.eleanor.close.period.wizard'].create(vals)
        return {
            'name':"Cerrar periodo",
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'pabs.eleanor.close.period.wizard',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wizard_id.id,
        }  
        return True            