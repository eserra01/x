# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ContractStatusReason(models.Model):
    """Modelo que contiene los motivos de los estatus asignados a los contratos"""
    _name = "pabs.contract.status.reason"
    _description = "Motivos de estatus de contratos"
    _rec_name = "reason"

    status_id = fields.Many2one(string="Estatus", comodel_name="pabs.contract.status", required = True)
    reason = fields.Char(string="Motivo")
    
    _sql_constraints = [
        ('unique_reason',
        'UNIQUE(status_id, reason)',
        'No se puede crear el registro: ya existe ese motivo en ese estatus'),
    ]