# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ComissionTemplateOfTemplates(models.Model):
    """Modelo que contiene la plantilla que se utilizaran al crear las plantillas"""
    _name = "pabs.comission.template.of.templates"
    _description = "Plantilla de plantillas de comisiones"

    plan_id = fields.Many2one(string="Plan", comodel_name="product.pricelist.item", required=True, tracking=True)

    pay_order = fields.Integer(string="Prioridad", required = True, tracking=True)

    job_id = fields.Many2one(string="Cargo", comodel_name="hr.job", required=True, tracking=True)

    active = fields.Boolean(string = "Activo", default = "True", required="True", tracking=True)

    company_id = fields.Many2one(
        'res.company', 'Compañia', required=True,
        default=lambda s: s.env.company.id, index=True)

    # No permitir registrar dos cargos en la misma plantilla (la llave se compone de id_plan, id_cargo)
    _sql_constraints = [
        ('unique_template_entry',
        'UNIQUE(plan_id, job_id)',
        'No se puede crear el registro: ya existe una fila con los mismos datos -> [plan, cargo]'),

        ('unique_order_entry',
        'UNIQUE(plan_id, pay_order)',
        'No se puede crear el registro: ya existe una fila con los mismos datos -> [plan, orden]')
    ]

    #0% Definir cargos que se podrán seleccionar (actual: departamento de ventas)