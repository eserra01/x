# -*- encoding: utf-8 -*-

from odoo import models
from odoo.exceptions import UserError

class PackXlsxReport(models.AbstractModel):
    _name = 'report.pabs_compensations.bonus_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, recs):
        # Se define estilos
        sheet = workbook.add_worksheet("Bonos mensuales")
        bold = workbook.add_format({'bold': True,'fg_color':'#4285F4'})
        total = workbook.add_format({'bold': True,'fg_color':'#CCCCCC'})
        normal = workbook.add_format({'bold': False})
        
        # Anchos de columna
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 50)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 15)
        
        # Encabezados
        sheet.write(0, 0, 'CÓDIGO', bold)
        sheet.write(0, 1, 'EMPLEADO', bold)
        sheet.write(0, 2, 'PUESTO', bold)
        sheet.write(0, 3, 'OFICINA', bold)
        sheet.write(0, 4, 'MONTO', bold)        

        # Se obtienen los bonos
        bonus_ids = self.env['pabs.compensation'].search(
        [
            ('start_date','>=',data.get('start_date')),
            ('end_date','<=',data.get('end_date')),
            ('company_id','=',self.env.company.id),
        ])       

        # Se obtienen las lineas de todas las oficinas
        line_ids = self.env['pabs.compensation.line'].search([('compensation_id','in',(bonus_ids.ids))])
        line_ids = line_ids.sorted(key=lambda r: r.warehouse_id.name)
        # Se obtienen los empleados
        employee_ids = line_ids.mapped('employee_id')
        
        # Si hay bonos   
        if line_ids:
            #
            i = 1                                                                 
            # Para cada linea del bono              
            for line in line_ids:
                #
                if line.amount > 0:                                  
                    sheet.write(i, 0, line.employee_id.barcode, normal)
                    sheet.write(i, 1, line.employee_id.name, normal)
                    sheet.write(i, 2, dict(line._fields['type'].selection).get(line.type), normal)
                    sheet.write(i, 3, line.warehouse_id.name, normal)
                    sheet.write(i, 4, round(line.amount,2), normal)                          
                    i+=1   
            
            # Totales por empleado
            i += 3
            # Encabezados
            sheet.write(i, 0, 'CÓDIGO', bold)
            sheet.write(i, 1, 'EMPLEADO', bold)            
            sheet.write(i, 2, 'TOTAL', bold)
            i+=1
            # Para cada empleado  
            for employee_id in employee_ids:
                # Se obtiene el total
                total = sum(line_ids.filtered(lambda r: r.employee_id.id == employee_id.id).mapped('amount'))
                # Si es mayor a cero 
                if total:                                                            
                    sheet.write(i, 0, employee_id.barcode, normal)
                    sheet.write(i, 1, employee_id.name, normal)               
                    sheet.write(i, 2, round(total,2), normal)                          
                    i+=1  


