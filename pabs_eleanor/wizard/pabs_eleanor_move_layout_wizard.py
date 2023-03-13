# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class EleanorMoveLayout(models.TransientModel):
  _name = 'pabs.eleanor.move.layout'
  _description = 'Plantilla de carga de movimientos en Eleanor'

  period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo de periodo", required=True)

  def generate_xls_report(self):
    data = {
       'period_type': self.period_type,
       'period_name': dict(self._fields['period_type'].selection).get(self.period_type)
    }

    return self.env.ref('pabs_eleanor.pabs_eleanor_move_layout_xlsx_report_id').report_action(self, data=data)
  
class PabsEleanorMoveLayoutXlsxReport(models.AbstractModel):
    _name = 'report.pabs_eleanor.pabs_eleanor_move_layout_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, recs):

        sheet = workbook.add_worksheet("Plantilla de carga {}".format(data['period_name']))
        bold = workbook.add_format({'bold': True})
        normal = workbook.add_format({'bold': False})
        
        # Columnas de Encabezados            
        sheet.write(0, 0, 'Código de empleado', bold)
        sheet.write(0, 1, 'Nombre del empleado', bold)
        sheet.write(0, 2, 'Oficina', bold)            
        sheet.write(0, 3, 'Puesto', bold)                               

        ### Columnas de Percepciones   
        perception_ids = self.env['pabs.eleanor.concept'].search(
        [
            ('concept_type','=','perception'),
            ('allow_load','=',True)
        ], order='order asc')
        
        for y,rec in enumerate(perception_ids,start=4):               
            sheet.write(0, y, rec.name, bold)
            i = y
        
        ### Columnas de Deducciones             
        deduction_ids = self.env['pabs.eleanor.concept'].search(
        [
            ('concept_type','=','deduction'),
            ('allow_load','=',True)
        ], order='order asc')
                    
        for y,rec in enumerate(deduction_ids,start=i+1):             
            sheet.write(0, y, rec.name, bold)     

        # Filas de Empleados (Solo los que tiene acceso)
        all_employees_allowed = self.env.user.all_employees

        employe_ids = []
        if all_employees_allowed:
            employe_ids = self.env['hr.employee'].search(
            [
                ('company_id', '=', self.env.company.id),
                ('employee_status.name', '=', 'ACTIVO'),
                ('period_type', '=', data['period_type'])
            ], order='barcode ASC')
        else:
            accesos = self.env['pabs.eleanor.user.access'].search([
                ('company_id', '=', self.env.company.id),
                ('user_id', '=', self.env.user.id)
            ])

            if accesos:

                ids_departamentos = accesos.mapped('department_id').ids
                ids_oficinas = accesos.mapped('warehouse_id').ids

                employe_ids = self.env['hr.employee'].search(
                [
                    ('company_id', '=', self.env.company.id),
                    ('employee_status.name', '=', 'ACTIVO'),
                    ('period_type', '=', data['period_type']),
                    '|', ('department_id', 'in', ids_departamentos), ('warehouse_id', 'in', ids_oficinas)
                ], order='barcode ASC')
        
        for i,rec in enumerate(employe_ids,start=1):         
            sheet.write(i, 0, rec.barcode or '', normal)
            sheet.write(i, 1, rec.name, normal)
            sheet.write(i, 2, rec.warehouse_id.name if rec.warehouse_id else rec.department_id.name or '', normal)   
            sheet.write(i, 3, rec.job_id.name or '', normal)