# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ComissionDebtCollector(models.Model):
    """Modelo que contiene la información de comisiones del cobrador"""
    _name = "pabs.comission.debt.collector"
    _description = "Comisiones de cobradores"

    debt_collector_id = fields.Many2one(string="Cobrador", comodel_name="hr.employee", required=True)
    comission_percentage = fields.Float(string="Comision", default = 0, tracking=True)
    comission_percentage_with_salary = fields.Float(string="Comision con sueldo", default = 0, tracking=True)
    comission_percentage_pantheon = fields.Float(string="Comision de Panteón", default = 0, tracking=True)
    effectiveness = fields.Float(string="Efectividad", default = 0, tracking=True)
    has_salary = fields.Boolean(string = "Es de sueldo", default = False, tracking=True)
    receipt_series = fields.Char(string = "Serie de recibos", tracking = True)

    #Serie unica de recibos
    _sql_constraints = [
        ('unique_receipt_series',
        'UNIQUE(receipt_series)',
        'No se puede crear el registro: un cobrador ya tiene asignada esa serie de recibos'),

        ('unique_debt_collector',
        'UNIQUE(debt_collector_id)',
        'No se puede crear el registro: ya existe un registro en esta tabla para el cobrador que se quiere crear')
    ]