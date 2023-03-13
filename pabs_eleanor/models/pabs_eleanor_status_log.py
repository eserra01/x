# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorStatusLog(models.Model):
    _name = 'pabs.eleanor.status.log'
    _description = 'Log de cambio de estatus'
    _rec_name = 'employee_status_id'
    _order = 'id desc'

    employee_status_id = fields.Many2one(comodel_name="hr.employee.status", string="Estatus", required=True)
    status_date = fields.Date(string="Fecha", required=True)
    comments = fields.Char(string="Comentarios", required=True)
    attachment_name = fields.Char(string="Adjunto")
    attachment_file = fields.Binary(string="Adjunto")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 

    @api.model
    def create(self, vals):
        rec = super(PabsEleanorStatusLog, self).create(vals)

        ### No cambiar estatus en la migracion
        if self.env.context.get('migration'):
            return rec
        
        # Se actualiza el estatus y fecha
        rec.employee_id.employee_status = rec.employee_status_id.id
        rec.employee_id.employee_status_date = rec.status_date
        return rec
