# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ComissionTree(models.Model):
    """Modelo que contiene los árboles de comisión de los contratos"""
    _name = "pabs.comission.tree"
    _description = "Árboles de comision de contratos"

    contract_id = fields.Many2one(string="Contrato", comodel_name="pabs.contract")#, readonly=True)
    
    pay_order = fields.Integer(string="Prioridad")

    job_id = fields.Many2one(string="Cargo", comodel_name="hr.job")

    comission_agent_id = fields.Many2one(string="Comisionista", comodel_name="hr.employee")
    
    corresponding_commission = fields.Float(string="Comision correspondiente", default = 0)#, readonly=True)
    remaining_commission = fields.Float(string="Comision restante", default = 0)#, readonly=True)
    commission_paid = fields.Float(string="Comision pagada", default = 0)#, readonly=True)
    actual_commission_paid = fields.Float(string="Comision real pagada", default = 0)#, readonly=True)

    _sql_constraints = [
        ('unique_comission_entry',
        'UNIQUE(contract_id, pay_order, job_id)',
        'No se puede crear el registro: ya existe el cargo a insertar en el árbol'),

        # ('unique_priority',
        # 'UNIQUE(contract_id,pay_order)',
        # 'No se puede crear el registro: ya existe el orden a insertar en el árbol'),
    ]

#Para papeleria y bono
    def CrearSalidasEnganche(self, IdPago, NumeroContrato, MontoPago, TipoPago):
        # IdPago = 1
        # NumeroContrato = 'C00000002'
        # MontoPago = 50000
        # TipoPago = "Bono"

        #Obtener y validar información del contrato
        contrato = self.env['pabs.contract'].search([('name', '=', NumeroContrato)])

        if not contrato.id:
            raise ValidationError("No se encontró el contrato {}".format(NumeroContrato))

        #Instanciar objeto Salida de comisiones
        salida_comisiones_obj = self.env['pabs.comission.output']

        ######################## PAPELERIA ##########################
        if TipoPago == "Papeleria":
            #Obtener id del cargo
            id_cargo = self.env['hr.job'].search([('name', '=', "Papeleria")]).id

            #Obtener registro de papeleria en el árbol de comisiones
            registro_arbol = self.search(['&',('contract_id', '=', contrato.id), ('job_id', '=', id_cargo)])

            if not registro_arbol:
                raise ValidationError("No se encontro el monto de papeleria en el árbol de comisiones")

            #Validar que el monto de pago sea igual al de la papeleria
            if MontoPago != registro_arbol.corresponding_commission:
                raise ValidationError("El monto de pago = ({}) es diferente a la comisión de papelería =  ({})".format(MontoPago, registro_arbol.corresponding_commission))
            
            #Validar que aun queda comisión por restar
            if registro_arbol.remaining_commission <= 0:
                raise ValidationError("La comisión restante de Papeleria ya se encuentra en cero")

            #Actualizar arbol
            registro_arbol.write({"commission_paid":MontoPago, "actual_commission_paid":MontoPago, "remaining_commission":0})

            #Crear registro en salida de comisiones
            salida_comisiones_obj.create([{"payment_id":IdPago, "job_id": registro_arbol.job_id.id, "comission_agent_id": registro_arbol.comission_agent_id.id, "commission_paid":MontoPago, "actual_commission_paid": MontoPago}])
        
        ######################## BONO ##########################
        elif TipoPago == "Bono":

            #Obtener id del cargo
            id_cargo = self.env['hr.job'].search([('name', '=', "Fideicomiso")]).id

            #Obtener registro de papeleria en el árbol de comisiones
            registro_arbol = self.search(['&',('contract_id', '=', contrato.id), ('job_id', '=', id_cargo)])

            if not registro_arbol:
                raise ValidationError("No se encontro el monto de Fideicomiso en el árbol de comisiones")
            
            #Validar que el monto de pago sea menor o igual a la comision restante
            if registro_arbol.remaining_commission < MontoPago:
                raise ValidationError("El monto del bono = ({}) es mayor a la comision restante del Fideicomiso = ({})".format(MontoPago, registro_arbol.remaining_commission))

            #Validar que aun queda comisión por restar
            if registro_arbol.remaining_commission <= 0:
                raise ValidationError("La comisión restante de Fideicomiso ya se encuentra en cero")

            #Actualizar arbol
            comisionRestante = registro_arbol.remaining_commission - MontoPago
            registro_arbol.write({"commission_paid":MontoPago, "actual_commission_paid":MontoPago, "remaining_commission": comisionRestante})

            #Crear registro en salida de comisiones
            salida_comisiones_obj.create([{"refund_id":IdPago, "job_id": registro_arbol.job_id.id, "comission_agent_id": registro_arbol.comission_agent_id.id, "commission_paid":MontoPago, "actual_commission_paid": MontoPago}])

#Para excedente y abono
    def CrearSalidas(self, IdPago, NumeroContrato, CodigoCobrador, MontoPago, EsExcedente = False):

        ################################################################################################################################################################
        ### PENDIENTE AL PASAR A GUADALAJARA: 10% de comisión al cobrador si el abono se hizo dentro de los primeros 3 meses a partir de la fecha de primer abono    ###
        ################################################################################################################################################################

        # IdPago = 4
        # NumeroContrato = 'C00000002'
        # CodigoCobrador = 'C0001'
        # MontoPago = 100
        # EsExcedente = False

        #Validar información del recibo
        if MontoPago < 0:
            raise ValidationError("El monto del recibo = ({}) es menor a cero".format(MontoPago))

        #Obtener y validar información del contrato
        contrato = self.env['pabs.contract'].search([('name', '=', NumeroContrato)])

        if not contrato.id:
            raise ValidationError("No se encontró el contrato {}".format(NumeroContrato))
        
        #Obtener y validar información del arbol de comisiones
        arbol = self.search([('contract_id', '=', contrato.id)], order='pay_order asc')

        if not arbol:
            raise ValidationError("No se encontro el árbol de comisiones")

        #Instanciar objeto Salida de comisiones
        salida_comisiones_obj = self.env['pabs.comission.output']

        ### Comienza proceso de cobrador ###
        #Calcular porcentaje del cobrador
        PorcentajeCobrador = 0
        if EsExcedente:
            PorcentajeCobrador = 0
        else:
            #Obtener y validar información del cobrador
            empleado = self.env["hr.employee"].search([('barcode', '=', CodigoCobrador)])

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
            id_cargo_cobrador = self.env['hr.job'].search([('name', '=', "Cobrador")]).id
            registroCobradorEnArbol = self.search([('contract_id','=', contrato.id),('comission_agent_id', '=', empleado.id), ('job_id', '=', id_cargo_cobrador)], limit = 1)

            if registroCobradorEnArbol:
                #Actualizar registro en Arbol
                AcumuladoMontoComisionCobrador = registroCobradorEnArbol.actual_commission_paid + MontoComisionCobrador
                registroCobradorEnArbol.write({"actual_commission_paid": AcumuladoMontoComisionCobrador})
            else:
                #No crear linea en el arbol si el cobrador no recibió comisión
                if PorcentajeCobrador > 0:
                    #Obtener ultimo orden del arbol de comisiones
                    siguiente_orden_disponible = arbol.search([], order='pay_order desc', limit = 1).pay_order + 1
                    #Crear registro en Arbol
                    self.create([{"contract_id":contrato.id, "pay_order":siguiente_orden_disponible, "job_id":id_cargo_cobrador, "comission_agent_id":empleado.id, "actual_commission_paid":MontoComisionCobrador}])

            #Insertar linea de cobrador en salida de comisiones
            salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":id_cargo_cobrador, "comission_agent_id":empleado.id, "actual_commission_paid": MontoComisionCobrador}])

        ### REALIZAR PROCESO PARA EMPLEADOS DEL ÁRBOL
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
                    salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id":com.comission_agent_id.id, "commission_paid":comisionPagadaSalida, "actual_commission_paid": comisionRealPagadaSalida}])
                else:
                #Si el monto de pago no cubre la comisión restante
                    comisionPagadaSalida = MontoPago                                        #1.1 Comision pagada de salida = Monto_pago
                    comisionRealPagadaSalida = MontoPago - (MontoPago * PorcentajeCobrador) #1.2 Comision real pagada de salida = Monto_pago - (Monto_pago * Porcentaje_cobrador)

                    comisionPagada = comisionPagada + MontoPago                             #2.1 Comision a pagar = Monto_pago
                    comisionRealPagada = comisionRealPagada + comisionRealPagadaSalida      #2.2 Comisión real pagada de arbol = Comision_real_pagada + Comision_real_pagada_salida
                    comisionRestante = comisionRestante - MontoPago                         #2.3 Comision restante = Comision_restante - Monto_pago
                    MontoPago = 0                                                           #4. Disminuir el monto del abono = 0

                    #Actualizar arbol
                    com.write({"commission_paid":comisionPagada, "actual_commission_paid":comisionRealPagada, "remaining_commission":comisionRestante})

                    #Crear registro en salida de comisiones
                    salida_comisiones_obj.create([{"payment_id":IdPago, "job_id":com.job_id.id, "comission_agent_id":com.comission_agent_id.id, "commission_paid":comisionPagadaSalida, "actual_commission_paid": comisionRealPagadaSalida}])

                    #Al no quedar mas por repartir se termina el proceso
                    break
        