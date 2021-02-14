from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

class CarnetPagoWizard(models.TransientModel):
    _name = 'report.carnet.pago'

    print_by_range = fields.Boolean(
        string='Impresión por rango',
        default=True,
    )

    date_from = fields.Date(
        string='Inicial',
    )
    date_to = fields.Date(
        string='Final',
    )

    office = fields.Selection([
        ('1', 'OFICINA VENTAS1'),
        ('2', 'OFICINA VENTAS2'),
        ('3', 'OFICINA VENTAS3'),
        ('4', 'OFICINA VENTAS4'),
        ('5', 'OFICINA VENTAS5'),
        ('6', 'OFICINA VENTAS6'),
        ('7', 'OFICINA VENTAS7'),
        ('8', 'OFICINA VENTAS8'),
    ],
        string='Oficina',
    )

    contract_number = fields.Char(
        string='Contrato',
    )

    no_copies = fields.Selection([
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    ],
        string='No. copias',
    )

    def filter(self):
        print('--------------------------filter-------------------------------')
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_from,
                'date_end': self.date_to,
            },
        }
        print('data', data)
        print("cccccc")
        return self.env.ref('xmarts_funeraria.id_carnet_pago').report_action(self, data=data)


# class ReportAttendanceRecapINGEGRE(models.AbstractModel):

#     _name = "report.xmarts_funeraria.payroll_ing_egre"

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         date_start = data['form']['date_start']
#         date_end = data['form']['date_end']

#         print("xxxxxxx",date_start)
#         employee = self.env['hr.employee'].search([
#                 ('id', '>', 0),
#             ])

#         docs = []
#         for emp in employee:
#             print("CCCCC",emp.name)

#             docs.append({
#                 'partner': emp.name,
#                 'code': emp.code_pabs,
#             })

#         return {
#             'date_start': date_start,
#             'date_end': date_end,
#             'docs': docs,
#         }
