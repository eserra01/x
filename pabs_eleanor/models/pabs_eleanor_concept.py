# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEleanorConcept(models.Model):
    _name = 'pabs.eleanor.concept'
    _description = 'Conceptos'    

    name = fields.Char(string="Concepto", required=True)
    name2 = fields.Char(string="Concepto nómina", required=True)
    category_id = fields.Many2one(comodel_name="pabs.eleanor.concept.category", string="Categoría", required=True)
    account_id = fields.Many2one(comodel_name="account.account", string="Cuenta", required=True)
    concept_type = fields.Selection([('perception','Percepcion'),('deduction','Deducción')], string="Tipo concepto", required=True)
    order = fields.Integer(string="Orden", required=True)
    allow_load = fields.Boolean(string="Permitir carga")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 

    @api.constrains('order')
    def _check_order(self):       
        for record in self:  
            concept_id = self.search(
                [
                    ('id','!=',record.id),
                    ('concept_type','=',record.concept_type),
                    ('order','=',record.order),
                    ('company_id','=',self.env.company.id)])
            if concept_id:
                raise ValidationError("Ya existe un registro con el orden y tipo seleccionados") 

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name, company_id)',  'Ya existe un registro con el nombre seleccionado.'),               
    ]

