# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date

ESTATUS = [
    ('sin_cierre','Sin cierre'),    #Se acaba de generar el contrato y no tiene cierre
    ('cerrado', 'Con cierre'),      #El contrato ya tiene un cierre. Ya se muestra en el reporte
    ('confirmado', 'Confirmado')    #Se confirma que ya se tiene el dinero del contrato
]

class PabsAccountMove(models.Model):
    _name = 'pabs.econtract.move'
    _descripcion = "Generador de pólizas de Inversiones y Excedentes de afiliaciones electrónicas"
    _rec_name = 'id_contrato'

    company_id = fields.Many2one(string="Compañia", comodel_name="res.company")
    id_asistente = fields.Many2one(string="Asistente", comodel_name="hr.employee")
    id_contrato = fields.Many2one(string="Contrato", comodel_name="pabs.contract")
    id_oficina = fields.Many2one(string="Oficina", related="id_contrato.lot_id.warehouse_id")

    periodo = fields.Integer(string="Periodo")
    fecha_hora_cierre = fields.Datetime(string="Fecha y hora de cierre")

    id_poliza_caja_transito = fields.Many2one(string="Poliza caja tránsito", comodel_name = "account.move")
    id_poliza_caja_electronicos  = fields.Many2one(string="Poliza caja electrónicos", comodel_name = "account.move")
    
    estatus = fields.Selection(selection=ESTATUS, string='Estado', default='sin_cierre')

    @api.depends('fecha_hora_cierre')
    def CalcularFechaCierre(self):
        for rec in self:
            if rec.fecha_hora_cierre:
                rec.fecha_cierre = fields.Date.to_date(rec.fecha_hora_cierre)
            else:
                rec.fecha_cierre = date(1900, 1, 1)