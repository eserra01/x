# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ComissionOutput(models.Model):
    """Modelo que contiene las salidas de comisiones de los pagos"""
    _name = "pabs.comission.output"
    _description = "Salida de comisión de los pagos"

    payment_id = fields.Many2one(string="Pago", comodel_name="account.payment")#, readonly=True)
    refund_id = fields.Many2one(string="Nota", comodel_name="account.move")#, readonly=True)

    job_id = fields.Many2one(string="Cargo", comodel_name="hr.job")#, readonly=True)
    comission_agent_id = fields.Many2one(string="Comisionista", comodel_name="hr.employee")#, readonly=True)
    commission_paid = fields.Float(string="Comision pagada", default = 0)#, readonly=True)
    actual_commission_paid = fields.Float(string="Comision real pagada", default = 0)#, readonly=True)

    # Fecha_oficina relacionado al pago
    payment_date = fields.Date(comodel_name='account.payment', related="payment_id.payment_date", string='Fecha de oficina')
    payment_status = fields.Selection(comodel_name='account.payment', related="payment_id.state", string='Estatus')
