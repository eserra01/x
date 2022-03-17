# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEcontractWizard(models.TransientModel):
    _name = 'pabs.econtract.wizard.by.range'

    initial_contract = fields.Many2one(comodel_name="pabs.contract", domain="([('state','=','contract')])", string="Contrato inicial")
    final_contract = fields.Many2one(comodel_name="pabs.contract", domain="([('state','=','contract')])", string="Contrato final")

    def Imprimir(self):
        ### Validar que existe reporte ###
        reporte = self.env['ir.actions.report'].sudo().search([
            ('template_id.company_id.id', '=', self.env.company.id),
            ('name', '=', 'contrato_premium')
        ])

        if not reporte:
            raise ValidationError("No existe el reporte {}".format('contrato_premium'))

        ### Obtener ids de contratos ###
        id_contratos = self.env['pabs.contract'].search([
            ('company_id', '=', self.env.company.id),
            ('name', '>=', self.initial_contract.name),
            ('name', '<=', self.final_contract.name)
        ], order="name")

        if not id_contratos:
            raise ValidationError("No se encontraron contratos")

        return reporte.report_action(id_contratos)