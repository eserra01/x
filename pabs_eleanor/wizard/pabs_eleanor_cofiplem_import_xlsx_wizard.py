# -*- encoding: utf-8 -*-
from odoo import models, fields,_
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class PabsEleanorCofiplemImportImportXLSWizard(models.Model):
    _name = 'pabs.eleanor.cofiplem.import.xls.wizard'
    
    option = fields.Selection([('taxpayer','Contribuyente'),('ema','EMA'),('eba','EBA')], string="Tabla destino")
    file = fields.Binary(string="Archivo", required=True)
    file_name = fields.Char(string="Archivo")         
    info = fields.Char(string="Resultados",default="", readonly=True)         

    def import_file(self):       
        wb = openpyxl.load_workbook( 
        filename=BytesIO(base64.b64decode(self.file)), read_only=True)
        ws = wb.active                    
        records = ws.iter_rows(min_row=2, max_row=None, min_col=None,max_col=None, values_only=True)
        
        employee_obj = self.env['hr.employee']
        # CONTRIBUYENTES
        if self.option == 'taxpayer': 
            taxpayer_obj = self.env['pabs.eleanor.taxpayer']                                        
            for i,record in enumerate(records,1):
                vals = {
                    'taxpayer': record[1], 
                    'rfc': record[2], 
                    'curp': record[3],
                    'address': record[4],
                    'imss_class': record[5],
                    'register_date': record[6],
                    'boss_register': record[7],                                       
                }
                taxpayer_obj.create(vals)        
        # EMA            
        if self.option == 'ema':           
            ema_obj = self.env['pabs.eleanor.ema']                                                    
            for i,record in enumerate(records,1):
                # Se busca el empleado mediante el NSS
                employee_id = employee_obj.search([('nss','=',record[0])])
                # if not employee_id:
                #     raise ValidationError("No se encuentra el empleado con el NSS: {}".format(record[0]))
                vals = {
                    'nss': record[0] or "",
                    'full_name': record[1] or "",
                    'move_origin': record[2] or "",
                    'move_type': record[3] or "",
                    'move_date': record[4] or "",
                    'days': record[5] or "",
                    'salary': record[6] or "",
                    'fixed_fee': record[7] or "",
                    'exce_boss': record[8] or "",
                    'exce_worker': record[9] or "",
                    'pres_money_boss': record[10] or "",
                    'pres_money_worker': record[11] or "",
                    'gmp_boss': record[12] or "",
                    'gmp_worker': record[13] or "",
                    'work_risk': record[14] or "",
                    'i_boss_life': record[15] or "",
                    'i_worker_life': record[16] or "",
                    'social_benefits': record[17] or "",
                    'total': record[18] or "",
                    'company': record[19] or "",
                    'period': record[20] or "",
                    'boss_register': record[21] or "",
                    'ema_id': record[22] or "",
                    'branch': record[23] or "",
                    'internal_period': record[24] or "",
                    'employee_id': employee_id.id or None
                }
                ema_obj.create(vals)                     
        # EBA
        if self.option == 'eba':           
            eba_obj = self.env['pabs.eleanor.eba']                                        
            for i,record in enumerate(records,1):
                 # Se busca el empleado mediante el NSS
                employee_id = employee_obj.search([('nss','=',record[0])])
                # if not employee_id:
                #     raise ValidationError("No se encuentra el empleado con el NSS: {}".format(record[0]))
                vals = {
                    'nss': record[0] or "",
                    'full_name': record[1] or "",
                    'move_origin': record[2] or "",
                    'move_type': record[3] or "",
                    'move_date': record[4] or "",
                    'days': record[5] or "",
                    'salary': record[6] or "",
                    'withdrawal': record[7] or "",
                    'ceav_boss': record[8] or "",
                    'ceav_worker': record[9] or "",
                    'rcv': record[10] or "",
                    'boss_input': record[11] or "",
                    'discount_type': record[12] or "",
                    'discount_value': record[13] or "",
                    'credit_number': record[14] or "",
                    'amortization': record[15] or "",
                    'infonavit': record[16] or "",
                    'total': record[17] or "",               
                    'company': record[18] or "",
                    'period': record[19] or "",
                    'boss_register': record[20] or "",
                    'eba_id': record[21] or "",
                    'branch': record[22] or "",
                    'internal_period': record[23] or "",
                    'employee_id': employee_id.id or None
                }
                eba_obj.create(vals)         
            
        self.info = "Se importaron {} registros.".format(str(i))
        # Se devuelve el wizard con los resultados 
        return {
                'name':"Resultados de importación",
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'pabs.eleanor.cofiplem.import.xls.wizard',
                'domain': [],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self._ids[0],
        }  