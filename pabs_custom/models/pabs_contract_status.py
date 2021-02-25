# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ContractStatus(models.Model):
    """Modelo que contiene los estatus asignados a los contratos"""
    _name = "pabs.contract.status"
    _description = "Estatus de contratos"
    _rec_name = "status"

    status = fields.Char(string="Estatus")
    
    _sql_constraints = [
        ('unique_estatus',
        'UNIQUE(status)',
        'No se puede crear el registro: ya existe ese estatus'),
    ]