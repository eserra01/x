# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PABSContract(models.Model):
  _inherit = 'pabs.contract'

  ecobro_id = fields.Char(string='Ecobro ID')

  def fix_comissions(self):
    ### Declaramos objetos
    contract_obj = self.env['pabs.contract']
    job_obj = self.env['hr.job']
    employee_obj = self.env['hr.employee']

    ### Buscamos todos los contratos que sean de tipo "Sueldo"
    contract_ids = contrat_obj.search([
      ('payment_scheme_id','=','SUELDO')])

    ### RECORREMOS LOS CONTRATOS
    for contract_id in contract_ids:

      ### VALIDAMOS EL ARBOL DE COMISIONES
      comission_tree = contract_id.commission_tree

      ### BUSCAMOS LA LINEA DEL ASISTENTE SOCIAL
      assistent_line = comission_tree.filtered(lambda k: k.job_id.name == 'ASISTENTE SOCIAL')

      ### VALIDAMOS QUE EXISTE EL REGISTRO
      if assistent_line:
        ### VALIDAMOS QUE TENGA ALGÚN VALOR EN EL ARBOL DE COMISIÓN
        if assistent_line.corresponding_commission > 0:
          ### GUARDAMOS LOS VALORES
          corresponding_value = assistent_line.corresponding_commission
          remaining_value = assistent_line.remaining_commission
          paid_value = assistent_line.commission_paid
          actual_paid_value = assistent_line.actual_commission_paid

          ### BUSCAMOS LA LINEA DE FIDEICOMISO
          fide_line = comission_tree.filtered(lambda k: k.job_id.name == 'FIDEICOMISO')

          ### GUARDAMOS LA INFORMACION DEL FIDEICOMISO
          fide_corresponding = fide_line.corresponding_commission
          fide_remaining = fide_line.remaining_commission
          fide_paid = fide_line.commission_paid
          fide_actual_paid = fide_line.actual_commission_paid

          ### COMISION CORRESPONDIENTE
          fide_line.corresponding_commission = fide_corresponding + corresponding_value
          fide_line.remaining_commission = fide_remaining + remaining_value
          fide_line.commission_paid = paid_value + fide_paid
          fide_line.actual_commission_paid = actual_paid_value + fide_actual_paid


          ###  INICIALIZAMOS EL ASISTENTE EN 0
          assistent_line.corresponding_commission = 0
          assistent_line.remaining_commission = 0
          assistent_line.commission_paid = 0
          assistent_line.actual_commission_paid = 0

      #### VALIDAMOS LA SALIDA DE COMISIONES DE LOS PAGOS, Y TRAEMOS SOLAMENTE PAGOS DE TIPO "ABONO"
      payment_ids = contract_id.payment_ids.filtered(lambda k: k.reference in ('payment','surplus'))

      ### BUSCAMOS EL ID DEL JOB DE FIDEICOMISO
      fide_job = job_obj.search([
        ('name','=','FIDEICOMISO')],limit=1)

      ### BUSCAMOS EL EMPLEADO LLAMADO FIDEICOMISO
      fide = employee_obj.search([
        ('job_id','=',fide_job.id)],limit=1)

      ### RECORREMOS LOS PAGOS
      for payment_id in payment_ids:

        ### TRAEMOS LAS SALIDAS DE COMISIONES DEL PAGO DE FIDEICOMISO
        fide_payment_commission = payment_id.comission_output_ids.filtered(
          lambda k: k.job_id.name == 'FIDEICOMISO')

        ### TRAEMOS LAS SALIDAS DE COMISIONES DEL PAGO
        assistant_payment_commission = payment_id.comission_output_ids.filtered(
          lambda k: k.job_id.name == 'ASISTENTE SOCIAL')

        ### SI EN EL PAGO NO EXISTE FIDEICOMISO
        if assistant_payment_commission:
          if not fide_payment_commission:
            ### CAMBIAMOS LA LINEA DEL CARGO AL FIDEICOMISO
            assistant_payment_commission.job_id = fide_job.id
            ### CAMBIAMOS LA LINEA DEL COMISIONISTA AL FIDEICOMISO
            assistant_payment_commission.comission_agent_id = fide.id
          ### SI NO
          else:
            ### GUARDAMOS LOS DATOS DEL ASISTENTE
            assistant_paid = assistant_payment_commission.commission_paid
            assistant_real_paid = assistant_payment_commission.actual_commission_paid

            ### GUARDAMOS LOS DATOS DEL FIDEICOMISO
            fide_paid = fide_payment_commission.commission_paid
            fide_real_paid = fide_payment_commission.actual_commission_paid

            ### LE SUMAMOS LA INFORMACIÓN DEL ASISTENTE AL FIDEICOMISO
            fide_payment_commission.commission_paid = fide_paid + assistant_paid
            fide_payment_commission.actual_commission_paid = fide_real_paid + assistant_real_paid

            ### ELIMINAMOS LA LINEA
            assistant_payment_commission.unlink()

