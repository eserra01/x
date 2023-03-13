# -*- encoding: utf-8 -*-
from odoo import models, fields,_
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

from datetime import timedelta

class PabsEleanorClosePeriodWizard(models.Model):
    _name = 'pabs.eleanor.close.period.wizard'
            
    info = fields.Char(string="Info",default="", readonly=True)
    closed = fields.Boolean(string="Cerrado")

    def close_period(self):
        period_id = self.env['pabs.eleanor.period'].browse(self.env.context.get('active_id'))

        ### Registrar histórico de sueldos del periodo
        self.env['pabs.eleanor.salary.history'].create_salary_history(period_id.period_type, self.env.company.id)

        ### Cerrar periodo activo
        period_id.state = 'close'
        
        ### Abrir periodo siguiente (aquel cuya fecha inicial sea la fecha final del periodo anterior más un día)
        new_period = self.env['pabs.eleanor.period'].search([
            ('company_id', '=', self.env.company.id),
            ('period_type', '=', period_id.period_type),
            ('date_start', '=', period_id.date_end + timedelta(days = 1)),
            ('state', '=', 'close')
        ])

        if not new_period:
            raise ValidationError("No se encontró el periodo siguiente")
        
        new_period.state = 'open'

        self.info = "Periodo cerrado {} {}. Periodo abierto {} {}".format(period_id.period_type, period_id.week_number, new_period.period_type, new_period.week_number)
        self.closed = True

        # Se devuelve el wizard con los resultados
        return {
                'name':"Periodo cerrado",
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'pabs.eleanor.close.period.wizard',
                'domain': [],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self._ids[0],
        }  