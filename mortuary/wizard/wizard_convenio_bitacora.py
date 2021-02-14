from odoo import models, fields


class ConvenioBitacoraWizard(models.Model):
    _name = 'convenio'

    bitacora_id = fields.Many2one(
        "mortuary", string='Bitacora', readonly=True, required=True)
    pagos_line_ids = fields.One2many(
        "convenio.pagos.line",
        "convenio_id",
        string="Lineas de pago",
        required=True)

    def btn_convenio_pagos(self):
        return self.env.ref('mortuary.mortuary_report_agreement').report_action([], data={})


class LineasPagos(models.Model):
    _name = 'convenio.pagos.line'

    convenio_id = fields.Many2one(
        "convenio", string='rel', required=True)
    bitacor_id = fields.Many2one(
        "mortuary", string='Bitacora', readonly=True, related="convenio_id.bitacora_id")
    fecha = fields.Date(string="Fecha")
    monto = fields.Float(string="Monto")
    concepto = fields.Text(string="Concepto")
