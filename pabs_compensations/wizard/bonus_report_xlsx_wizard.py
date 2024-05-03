# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta



class BonusXlsxReportWizard(models.TransientModel):
    _name = "bonus.report.xlsx.wizard"
    _description = "Asistente reporte de bonos"
    
    start_date =fields.Date(string="Fecha inicial")
    end_date = fields.Date(string="Fecha final")
    company_id = fields.Many2one(comodel_name='res.company', string='Compañia', required=True, default=lambda s: s.env.company.id)

    @api.onchange('start_date')
    def _onchange_start_date(self):
        #
        if self.start_date:            
            #
            self.end_date = (self.start_date.replace(day=1) + relativedelta(months=1)) - relativedelta(days=1)
        
    def get_bonus_report_xlsx(self):
        data = {        
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        #   
        return self.env.ref('pabs_compensations.bonus_xlsx_report_id').report_action(self, data=data)

    