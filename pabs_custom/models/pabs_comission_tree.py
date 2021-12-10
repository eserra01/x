# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ComissionTree(models.Model):
    """Modelo que contiene los árboles de comisión de los contratos"""
    _name = "pabs.comission.tree"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Árboles de comision de contratos"

    contract_id = fields.Many2one(string="Contrato", comodel_name="pabs.contract", tracking=True)#, readonly=True)
    
    pay_order = fields.Integer(string="Prioridad", tracking=True)

    job_id = fields.Many2one(string="Cargo", comodel_name="hr.job", tracking=True)

    comission_agent_id = fields.Many2one(string="Comisionista", comodel_name="hr.employee", tracking=True)
    
    corresponding_commission = fields.Float(string="Comision correspondiente", default = 0, tracking=True)#, readonly=True)
    remaining_commission = fields.Float(string="Comision restante", default = 0, tracking=True)#, readonly=True)
    commission_paid = fields.Float(string="Comision pagada", default = 0, tracking=True)#, readonly=True)
    actual_commission_paid = fields.Float(string="Comision real pagada", default = 0, tracking=True)#, readonly=True)

    company_id = fields.Many2one(
        'res.company', 'Compañia', required=True,
        default=lambda s: s.env.company.id, index=True)

    _sql_constraints = [
        ('unique_comission_entry',
        'UNIQUE(contract_id, pay_order, job_id)',
        'No se puede crear el registro: ya existe el cargo a insertar en el árbol'),

        # ('unique_priority',
        # 'UNIQUE(contract_id,pay_order)',
        # 'No se puede crear el registro: ya existe el orden a insertar en el árbol'),
    ]

    #Para papeleria, bono y traspasos
    def CrearSalidasEnganche(self, IdPago, NumeroContrato, MontoPago, TipoPago):
        # IdPago = 1
        # NumeroContrato = 'C00000002'
        # MontoPago = 50000
        # TipoPago = "Bono"

        #Obtener y validar información del contrato
        contrato = self.env['pabs.contract'].browse(NumeroContrato)

        if not contrato.id:
            raise ValidationError("No se encontró el contrato {}".format(NumeroContrato))

        #Instanciar objeto Salida de comisiones
        salida_comisiones_obj = self.env['pabs.comission.output'].with_context(force_company=contrato.company_id.id)

    ######################## PAPELERIA ##########################
        if TipoPago == "Papeleria":
            #Obtener id del cargo
            cargo_papeleria = self.env['hr.job'].with_context(force_company=contrato.company_id.id).search([('name', '=', "PAPELERIA")])

            #Obtener registro de papeleria en el árbol de comisiones
            arbol_papeleria = contrato.commission_tree.filtered(lambda x: x.job_id.id == cargo_papeleria.id)

            if not arbol_papeleria:
                raise ValidationError("Contrato: {}\nNo se encontro el registro de papeleria en el árbol de comisiones".format(contrato.name))

            #Validar que el monto de pago sea igual al de la papeleria
            if MontoPago != arbol_papeleria.corresponding_commission:
                raise ValidationError("El monto de pago = ({}) es diferente a la comisión de papelería =  ({})".format(MontoPago, arbol_papeleria.corresponding_commission))
            
            #Validar que aun queda comisión por restar
            if arbol_papeleria.remaining_commission <= 0:
                raise ValidationError("La comisión restante de Papeleria ya se encuentra en cero")
            
             # FISCAL
            if contrato.company_id.apply_taxes:
                
                # Buscar impuesto IVA
                impuesto_IVA = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', contrato.company_id.id)]) # Buscar impuesto de IVA
                if not impuesto_IVA:
                    raise ValidationError("No se encontró el impuesto con nombre IVA")

                # Buscar puesto IVA
                cargo_iva = self.env['hr.job'].search([('name','=','IVA'), ('company_id','=', contrato.company_id.id)])
                if not cargo_iva:
                    raise ValidationError("No se encontró el puesto de trabajo con nombre IVA")

                # Buscar empleado IVA
                empleado_iva = self.env['hr.employee'].search([('barcode','=','IVA'), ('company_id','=', contrato.company_id.id)])
                if not empleado_iva:
                    raise ValidationError("No se encontró el empleado con código IVA")
                
                factor_iva = 1 + (impuesto_IVA.amount/100)
                monto_papeleria = round((MontoPago / factor_iva), 2)
                monto_iva = round( MontoPago - monto_papeleria, 2)

                #Crear registro de salidas
                salida_comisiones_obj.create([
                    {"payment_id":IdPago, "job_id": cargo_iva.id, "comission_agent_id": empleado_iva.id, "commission_paid": monto_iva, "actual_commission_paid": monto_iva, "company_id" : contrato.company_id.id},
                    {"payment_id":IdPago, "job_id": arbol_papeleria.job_id.id, "comission_agent_id": arbol_papeleria.comission_agent_id.id, "commission_paid": monto_papeleria, "actual_commission_paid": monto_papeleria, "company_id" : contrato.company_id.id}
                ])

                ### Actualizar montos en árbol (iva, papeleria y fideicomiso)

                # Disminuir iva a papeleria en "monto correspondiente"
                arbol_papeleria.write({"corresponding_commission": monto_papeleria, "commission_paid": monto_papeleria, "actual_commission_paid": monto_papeleria, "remaining_commission": 0})

                arbol_iva = contrato.commission_tree.filtered(lambda x: x.job_id.id == cargo_iva.id)
                if not arbol_iva:
                    raise ValidationError("Contrato: {}\nNo se encontro el registro de IVA en el árbol de comisiones".format(contrato.name))
                
                # iva
                comision_restante_iva = round(arbol_iva.remaining_commission - monto_iva, 2)
                arbol_iva.write({"commission_paid": monto_iva, "actual_commission_paid": monto_iva, "remaining_commission": comision_restante_iva})

                # Aumentar a fideicomiso el monto disminuido a papeleria
                cargo_fideicomiso = self.env['hr.job'].with_context(force_company=contrato.company_id.id).search([('name', '=', "FIDEICOMISO")])
                arbol_fideicomiso = contrato.commission_tree.filtered(lambda x: x.job_id.id == cargo_fideicomiso.id)
                correspondiente_fideicomiso = arbol_fideicomiso.corresponding_commission + monto_iva
                arbol_fideicomiso.write({"corresponding_commission": correspondiente_fideicomiso, "remaining_commission": correspondiente_fideicomiso})

            # NO FISCAL
            else: 
                #Actualizar arbol
                arbol_papeleria.write({"commission_paid":MontoPago, "actual_commission_paid":MontoPago, "remaining_commission":0})

                #Crear registro en salida de comisiones
                salida_comisiones_obj.create([{"payment_id":IdPago, "job_id": arbol_papeleria.job_id.id, "comission_agent_id": arbol_papeleria.comission_agent_id.id, "commission_paid":MontoPago, "actual_commission_paid": MontoPago, "company_id" : contrato.company_id.id}])
        
        ######################## BONO ##########################
        elif TipoPago in ("Bono", "Transfer"):

            #Obtener id del cargo
            cargo_fideicomiso = self.env['hr.job'].with_context(force_company=contrato.company_id.id).search([('name', '=', "FIDEICOMISO")])

            #Obtener registro de fideicomiso en el árbol de comisiones
            arbol_fideicomiso = contrato.commission_tree.filtered(lambda x: x.job_id.id == cargo_fideicomiso.id)

            if not arbol_fideicomiso:
                raise ValidationError("No se encontro el monto de Fideicomiso en el árbol de comisiones")
            
            # #Validar que el monto de pago sea menor o igual a la comision restante
            # if arbol_fideicomiso.remaining_commission < MontoPago:
            #     raise ValidationError("El monto del bono = ({}) es mayor a la comision restante del Fideicomiso = ({})".format(MontoPago, arbol_fideicomiso.remaining_commission))

            #Validar que aun queda comisión por restar
            if arbol_fideicomiso.remaining_commission <= 0:
                raise ValidationError("La comisión restante de Fideicomiso ya se encuentra en cero")
            
            # Si el monto del pago es mayor o igual que el saldo del contrato, se pagan todas las comisiones
            if MontoPago >= contrato.balance:
                # Obtenemos todas las lineas del arbol de comisiones
                for line in contrato.commission_tree:
                    line.remaining_commission = 0
                    line.commission_paid = line.corresponding_commission               
                    line.actual_commission_paid = line.corresponding_commission
            else:
                #Actualizar arbol
                comisionPagada = arbol_fideicomiso.commission_paid + MontoPago                 #2.1 Comision a pagar = Comision_pagada + Monto_pago
                comisionRealPagada = arbol_fideicomiso.actual_commission_paid + MontoPago      #2.2 Comisión real pagada de arbol = Comision_real_pagada + Comision_real_pagada_salida
                comisionRestante = arbol_fideicomiso.remaining_commission - MontoPago          #2.3 Comision restante = Comision_restante - Monto_pago
                #
                arbol_fideicomiso.write({"commission_paid":comisionPagada, "actual_commission_paid": comisionRealPagada, "remaining_commission": comisionRestante})

            #Crear registro en salida de comisiones
            if TipoPago == 'Bono':
                salida_comisiones_obj.create([
                {
                    "refund_id":IdPago, 
                    "job_id": arbol_fideicomiso.job_id.id, 
                    "comission_agent_id": arbol_fideicomiso.comission_agent_id.id, 
                    "commission_paid":MontoPago, 
                    "actual_commission_paid": MontoPago, 
                    "company_id" : contrato.company_id.id
                }])
            elif TipoPago == 'Transfer':
                salida_comisiones_obj.create([
                {
                    "payment_id":IdPago, 
                    "job_id": arbol_fideicomiso.job_id.id, 
                    "comission_agent_id": arbol_fideicomiso.comission_agent_id.id, 
                    "commission_paid":MontoPago, 
                    "actual_commission_paid": MontoPago, 
                    "company_id" : contrato.company_id.id
                }])


    #Para excedente y abono
    def CrearSalidas(self, IdPago, NumeroContrato, CodigoCobrador, MontoPago, EsExcedente = False):

        ################################################################################################################################################################
        ### PENDIENTE AL PASAR A GUADALAJARA: 10% de comisión al cobrador si el abono se hizo dentro de los primeros 3 meses a partir de la fecha de primer abono    ###
        ################################################################################################################################################################

        #Validar información del recibo
        if MontoPago < 0:
            raise ValidationError("El monto del recibo = ({}) es menor a cero".format(MontoPago))

        #Obtener contrato
        contrato = self.env['pabs.contract'].browse(NumeroContrato)

        if not contrato.id:
            raise ValidationError("No se encontró el contrato {}".format(NumeroContrato))
        
        #Obtener arbol de comisiones
        arbol = contrato.commission_tree.sorted(key = lambda x: x.pay_order)

        if not arbol:
            raise ValidationError("No se encontro el árbol de comisiones")

        salida_comisiones_obj = self.env['pabs.comission.output'].with_context(force_company=contrato.company_id.id)

        ##### CÁLCULO PARA COMISIONES DEL COBRADOR #####
        #Calcular porcentaje del cobrador
        PorcentajeCobrador = 0
        if EsExcedente:
            PorcentajeCobrador = 0
        else:
            #Obtener y validar información del cobrador
            empleado = self.env["hr.employee"].search([('barcode', '=', CodigoCobrador),('company_id', '=', contrato.company_id.id)])

            if not empleado:
                raise ValidationError("No se encontró el cobrador {}".format(CodigoCobrador))
            
            comisionesCobrador = self.env["pabs.comission.debt.collector"].search([('debt_collector_id', '=', empleado.id)])

            if not comisionesCobrador:
                raise ValidationError("No se encontró el porcentaje de comisión del cobrador {}".format(CodigoCobrador))

            if comisionesCobrador.has_salary:
                PorcentajeCobrador = comisionesCobrador.comission_percentage_with_salary / 100
            else:
                PorcentajeCobrador = comisionesCobrador.comission_percentage / 100

            #Calcular comisión del cobrador sobre el pago
            MontoComisionCobrador = MontoPago * PorcentajeCobrador

            #Obtener id del cargo de cobrador
            id_cargo_cobrador = self.env['hr.job'].search([('name', '=', "COBRADOR"),('company_id', '=', contrato.company_id.id)]).id
            registroCobradorEnArbol = contrato.commission_tree.filtered(lambda x: x.comission_agent_id.id == empleado.id and x.job_id.id == id_cargo_cobrador)

            if len(registroCobradorEnArbol) > 1:
                raise ValidationError("Se encontró mas de una linea en el árbol de comisiones {} del cobrador {}".format(contrato.name, empleado.name))

            if registroCobradorEnArbol:
                #Actualizar registro en Arbol
                AcumuladoMontoComisionCobrador = registroCobradorEnArbol.actual_commission_paid + MontoComisionCobrador
                registroCobradorEnArbol.write({"actual_commission_paid": AcumuladoMontoComisionCobrador})
            else:
                #No crear linea en el arbol si el cobrador no recibió comisión
                if PorcentajeCobrador > 0:
                    #Obtener ultima prioridad del arbol de comisiones
                    arbol_descendente = arbol.sorted(lambda r: r.pay_order, reverse = True)
                    siguiente_prioridad_disponible = arbol_descendente[0].pay_order + 1

                    #Crear registro en Arbol
                    self.create([{"contract_id":contrato.id, "pay_order": siguiente_prioridad_disponible, "job_id": id_cargo_cobrador, "comission_agent_id": empleado.id, "actual_commission_paid": MontoComisionCobrador, "company_id" : contrato.company_id.id}])

            #Insertar linea de cobrador en salida de comisiones
            salida_comisiones_obj.create([{"payment_id": IdPago, "job_id": id_cargo_cobrador, "comission_agent_id": empleado.id, "actual_commission_paid": MontoComisionCobrador, "company_id" : contrato.company_id.id}])

        ##### CÁLCULO PARA EMPLEADOS DEL ARBOL #####
        if contrato.company_id.apply_taxes: # FISCAL

            # Buscar impuesto IVA
            impuesto_IVA = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', contrato.company_id.id)]) # Buscar impuesto de IVA
            if not impuesto_IVA:
                raise ValidationError("No se encontró el impuesto con nombre IVA")

            # Buscar puesto IVA
            cargo_iva = self.env['hr.job'].search([('name','=','IVA'), ('company_id','=', contrato.company_id.id)])
            if not cargo_iva:
                raise ValidationError("No se encontró el puesto de trabajo con nombre IVA")

            factor_iva = 1 + (impuesto_IVA.amount/100)

            for com in arbol:
                
                # Cargo IVA
                if com.job_id.id == cargo_iva.id:
                    comision_iva = round( MontoPago - round(MontoPago / factor_iva, 2),  2)

                    #Crear registro en salida de comisiones
                    salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id": com.comission_agent_id.id, "commission_paid": comision_iva, "actual_commission_paid": comision_iva, "company_id" : contrato.company_id.id}])

                    #Actualizar arbol
                    com.write({"commission_paid": com.commission_paid + comision_iva, "actual_commission_paid": com.actual_commission_paid + comision_iva, "remaining_commission": com.remaining_commission - comision_iva})

                    MontoPago = MontoPago - comision_iva

                    #Ajuste a fideicomiso (el fideicomiso subsidia la comisión que debería de pagar el IVA al cobrador)
                    if PorcentajeCobrador > 0:
                        cargo_fideicomiso = self.env['hr.job'].with_context(force_company=contrato.company_id.id).search([('name', '=', "FIDEICOMISO"),('company_id','=',contrato.company_id.id)])
                        arbol_fideicomiso = contrato.commission_tree.filtered(lambda x: x.job_id.id == cargo_fideicomiso.id)
                        monto_ajuste_fideicomiso = (comision_iva * PorcentajeCobrador) * -1

                        #Crear registro en salida de comisiones
                        salida_comisiones_obj.create([{"payment_id":IdPago, "job_id": arbol_fideicomiso.job_id.id, "comission_agent_id": arbol_fideicomiso.comission_agent_id.id, "commission_paid": 0, "actual_commission_paid": monto_ajuste_fideicomiso, "company_id" : contrato.company_id.id}])

                        #Actualizar arbol
                        arbol_fideicomiso.write({"actual_commission_paid": arbol_fideicomiso.actual_commission_paid + monto_ajuste_fideicomiso})
                    
                    continue
                
                # Demas cargos
                if com.remaining_commission > 0 and MontoPago > 0:
                    comisionRestante = com.remaining_commission
                    comisionPagada = com.commission_paid
                    comisionRealPagada = com.actual_commission_paid

                    comisionPagadaSalida = 0
                    comisionRealPagadaSalida = 0

                    #Si el monto de pago cubre la comisión restante
                    if MontoPago >= com.remaining_commission:
                        comisionPagadaSalida = comisionRestante                             #1.1 Comision pagada de salida = Comision_restante
                        comisionRealPagadaSalida = comisionRestante - (comisionRestante * PorcentajeCobrador) #1.2 Comision real pagada de salida = Comision_restante - (Comision_restante * Porcentaje_cobrador)
                        
                        comisionPagada = comisionPagada + comisionRestante                  #2.1 Comision a pagar =  Comision_pagada + Comision_restante
                        comisionRealPagada = comisionRealPagada + comisionRealPagadaSalida  #2.2 Comisión real pagada de arbol = Comision_real_pagada + Comision_real_pagada_salida
                        comisionRestante = 0                                                #2.3 Comisión restante = 0
                        MontoPago = MontoPago - comisionPagadaSalida                        #3. Disminuir el monto del abono = Monto_pago - Comision_pagada
                        
                        #Actualizar arbol
                        com.write({"commission_paid":comisionPagada, "actual_commission_paid":comisionRealPagada, "remaining_commission":comisionRestante})

                        #Crear registro en salida de comisiones
                        salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id":com.comission_agent_id.id, "commission_paid":comisionPagadaSalida, "actual_commission_paid": comisionRealPagadaSalida, "company_id" : contrato.company_id.id}])
                    else:
                    #Si el monto de pago no cubre la comisión restante
                        comisionPagadaSalida = MontoPago                                        #1.1 Comision pagada de salida = Monto_pago
                        comisionRealPagadaSalida = MontoPago - (MontoPago * PorcentajeCobrador) #1.2 Comision real pagada de salida = Monto_pago - (Monto_pago * Porcentaje_cobrador)

                        comisionPagada = comisionPagada + MontoPago                             #2.1 Comision a pagar = Comision pagada + Monto_pago
                        comisionRealPagada = comisionRealPagada + comisionRealPagadaSalida      #2.2 Comisión real pagada de arbol = Comision_real_pagada + Comision_real_pagada_salida
                        comisionRestante = comisionRestante - MontoPago                         #2.3 Comision restante = Comision_restante - Monto_pago
                        MontoPago = 0                                                           #4. Disminuir el monto del abono = 0

                        #Actualizar arbol
                        com.write({"commission_paid":comisionPagada, "actual_commission_paid":comisionRealPagada, "remaining_commission":comisionRestante})

                        #Crear registro en salida de comisiones
                        salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id":com.comission_agent_id.id, "commission_paid":comisionPagadaSalida, "actual_commission_paid": comisionRealPagadaSalida, "company_id" : contrato.company_id.id}])

                        #Al no quedar mas por repartir se termina el proceso
                        break

        else: # NO FISCAL
            #Calcular cambios al árbol de comisiones y la salida de comisiones del recibo
            for com in arbol:
                
                if com.remaining_commission > 0 and MontoPago > 0:
                    comisionRestante = com.remaining_commission
                    comisionPagada = com.commission_paid
                    comisionRealPagada = com.actual_commission_paid

                    comisionPagadaSalida = 0
                    comisionRealPagadaSalida = 0

                    #Si el monto de pago cubre la comisión restante
                    if MontoPago >= com.remaining_commission:
                        comisionPagadaSalida = comisionRestante                             #1.1 Comision pagada de salida = Comision_restante
                        comisionRealPagadaSalida = comisionRestante - (comisionRestante * PorcentajeCobrador) #1.2 Comision real pagada de salida = Comision_restante - (Comision_restante * Porcentaje_cobrador)
                        
                        comisionPagada = comisionPagada + comisionRestante                  #2.1 Comision a pagar =  Comision_pagada + Comision_restante
                        comisionRealPagada = comisionRealPagada + comisionRealPagadaSalida  #2.2 Comisión real pagada de arbol = Comision_real_pagada + Comision_real_pagada_salida
                        comisionRestante = 0                                                #2.3 Comisión restante = 0
                        MontoPago = MontoPago - comisionPagadaSalida                        #3. Disminuir el monto del abono = Monto_pago - Comision_pagada
                        
                        #Actualizar arbol
                        com.write({"commission_paid":comisionPagada, "actual_commission_paid":comisionRealPagada, "remaining_commission":comisionRestante})

                        #Crear registro en salida de comisiones
                        salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id":com.comission_agent_id.id, "commission_paid":comisionPagadaSalida, "actual_commission_paid": comisionRealPagadaSalida, "company_id" : contrato.company_id.id}])
                    else:
                    #Si el monto de pago no cubre la comisión restante
                        comisionPagadaSalida = MontoPago                                        #1.1 Comision pagada de salida = Monto_pago
                        comisionRealPagadaSalida = MontoPago - (MontoPago * PorcentajeCobrador) #1.2 Comision real pagada de salida = Monto_pago - (Monto_pago * Porcentaje_cobrador)

                        comisionPagada = comisionPagada + MontoPago                             #2.1 Comision a pagar = Comision pagada + Monto_pago
                        comisionRealPagada = comisionRealPagada + comisionRealPagadaSalida      #2.2 Comisión real pagada de arbol = Comision_real_pagada + Comision_real_pagada_salida
                        comisionRestante = comisionRestante - MontoPago                         #2.3 Comision restante = Comision_restante - Monto_pago
                        MontoPago = 0                                                           #4. Disminuir el monto del abono = 0

                        #Actualizar arbol
                        com.write({"commission_paid":comisionPagada, "actual_commission_paid":comisionRealPagada, "remaining_commission":comisionRestante})

                        #Crear registro en salida de comisiones
                        salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id":com.comission_agent_id.id, "commission_paid":comisionPagadaSalida, "actual_commission_paid": comisionRealPagadaSalida, "company_id" : contrato.company_id.id}])

                        #Al no quedar mas por repartir se termina el proceso
                        break
            
    #Revierte las comisiones generadas por un pago. Actualiza los montos en el arbol de comisiones. Las salidas permanecen en el pago cancelado.
    def RevertirSalidas(self, IdPago, NumeroContrato, RefundID = False):

        #Obtener y validar información del contrato
        contrato = self.env['pabs.contract'].browse(NumeroContrato)

        if not contrato.id:
            raise ValidationError("No se encontró el contrato {}".format(NumeroContrato))

        #Obtener y validar información del arbol de comisiones
        arbol = contrato.commission_tree.sorted(key = lambda x: x.pay_order)

        if not arbol:
            raise ValidationError("No se encontro el árbol de comisiones")

        #Obtener y validar información de salida de comisiones
        if IdPago:
            salida_comisiones = self.env['pabs.comission.output'].search([('payment_id', '=', IdPago)])
        elif RefundID:
            salida_comisiones = self.env['pabs.comission.output'].search([('refund_id', '=', RefundID)])
        else:
            raise ValidationError("No se envió el ID del pago o de la nota")

        if not salida_comisiones:
            raise ValidationError("No se encontraron salidas de comisiones del pago")

        #Obtener id del cargo de cobrador
        id_cargo_cobrador = self.env['hr.job'].search([('name', '=', "COBRADOR"),('company_id', '=', contrato.company_id.id)]).id

        if not id_cargo_cobrador:
            raise ValidationError("No se encontró el id para el cargo Cobrador")

        ##### REALIZAR PROCESO PARA EMPLEADOS DEL ÁRBOL #####
        for salida in salida_comisiones:

            #Obtener registro en el árbol de comisiones
            com = arbol.filtered_domain(['&', ('comission_agent_id', '=', salida.comission_agent_id.id), ('job_id', '=', salida.job_id.id)])

            #Calcular nuevos montos
            comisionRestante = com.remaining_commission + salida.commission_paid
            comisionPagada = com.commission_paid - salida.commission_paid
            comisionRealPagada = com.actual_commission_paid - salida.actual_commission_paid

            #Si es cobrador y se quedó sin comisión: eliminar el registro del árbol. De lo contrario, actualizar.
            if com.job_id.id == id_cargo_cobrador:
                com.write({"actual_commission_paid":comisionRealPagada})
            else:
                com.write({"commission_paid":comisionPagada, "actual_commission_paid":comisionRealPagada, "remaining_commission":comisionRestante})