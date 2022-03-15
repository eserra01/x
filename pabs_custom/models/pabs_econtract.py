# -*- coding: utf-8 -*-

from asyncio.log import logger
from operator import truediv
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date

import requests
import logging
import json

_logger = logging.getLogger(__name__)

### MODIFICACIONES A OTROS MODULOS
# pabs_contract -> sección Buscar diario de efectivo -> Añadir compañia en búsqueda -> cash_journal_id = journal_obj.search([('company_id','=', previous.company_id.id), ('type','=','cash'), ('name','=','EFECTIVO')],limit=1)
# pabs_comission_tree -> cambiar force_company por agregar compañia en las búsquedas

### REGISTROS A CREAR
# Producto
# Tarifa
# Bonos
# Cuenta contable: 110.01.002 Afiliaciones electrónicas
# Cuenta contable: 101.01.004 Caja contratos electrónicos
# Cuenta contable: 101.01.005 Caja tránsito

### Sincronizadores a crear
# 1. Sincronizador de afiliaciones
# 2. Sincronizador de cortes
# 3. Sincronizador de cobradores asignados

CUENTA_TRANSITO = "101.01.005"
NOMBRE_CUENTA = "Caja transito"

class PABSElectronicContracts(models.TransientModel):
    _name = 'pabs.electronic.contract'
    _description = 'Afiliaciones electrónicas'

    ### Obtener web service de afiliaciones electrónicas ###
    # tipo 1 = consultar solicitudes
    # tipo 2 = confirmar creación de solicitudes
    def get_url(self, company_id, tipo):
        try:
            # Validar IP
            direccion_ip = self.env['res.company'].browse(company_id).ecobro_ip

            if not direccion_ip:
                raise ValidationError("No se ha asignado una IP en la compañia")
            
            #Asignar plaza #Actualizar al agregar otra plaza
            plaza_ecobro = ""
            if company_id == 12:
                if tipo in (5,6):
                    plaza_ecobro = "ecobroSAP_SALT"
                else:
                    plaza_ecobro = "asistencia_social_SLW"

            if not plaza_ecobro:
                ValidationError("No se ha definido la plaza de ecobro")
                return ""

            ### Asignar función ###
            metodo = ""
            # Sincronizar contratos
            if tipo == 1:
                metodo = "controlsolicitudes/getContratos"
            elif tipo == 2:
                metodo = "controlsolicitudes/setPendingContratosAsSync"
            #Sincronizar cortes
            elif tipo == 3:
                metodo = "controlsolicitudes/getContractsNotSynced"
            elif tipo == 4:
                metodo = "controlsolicitudes/updateContractsNotSynced"
            #Sincronizar cobradores asignados
            elif tipo == 5:
                metodo = "controlmapa/getContractsAssigned"
            elif tipo == 6:
                metodo = "controlmapa/updateContractsAssignedasSync"

            if not metodo:
                _logger.error("No se ha definido la plaza de ecobro")
                raise ValidationError("No se ha definido el método a llamar")
            
            return "http://{}/{}/{}".format(direccion_ip, plaza_ecobro, metodo)
        except Exception as ex:
            _logger.error("Error al consultar url {}")
            return ""

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def SincronizarContratos(self, company_id):
        _logger.info("Comienza sincronización de afiliaciones electrónicas")

        contract_obj = self.env['pabs.contract']

        ### Validar parámetros ###
        if not company_id:
            _logger.error("No se ha definido la compañia")
            return

        ### Validar cuentas para póliza ###
        info_de_cuentas = {}
        info_de_cuentas = self.ValidarCuentas(company_id, info_de_cuentas)
        if not info_de_cuentas:
            return

        ### Validar web service de consulta y respuesta ###
        url_obtener_afiliaciones = self.get_url(company_id, 1)
        if not url_obtener_afiliaciones:
            _logger.error("No se ha definido la dirección del web service: obtener afiliaciones electrónicas")
            return

        url_actualizar_afiliaciones = self.get_url(company_id, 2)
        if not url_actualizar_afiliaciones:
            _logger.error("No se ha definido la dirección del web service: actualizar afiliaciones electrónicas")
            return

        ### Llamar web service de consulta ###
        try:
            _logger.info("Comienza consulta de afiliaciones")
            respuesta = requests.post(url_obtener_afiliaciones)
            json_afiliaciones = json.loads(respuesta.text)
            array_solicitudes = json_afiliaciones.get('solicitudes')
        except Exception as ex:
            _logger.error("Error al consultar afiliaciones electrónicas {}".format(ex))
            return

        cantidad_afiliaciones = len(array_solicitudes)
        _logger.info("Afiliaciones obtenidas: {}".format(cantidad_afiliaciones))

        # TEST
        # for i in range(1, cantidad_afiliaciones): # Tomar solo X elementos de la lista
        #     array_solicitudes.pop(1)
        # cantidad_afiliaciones = len(array_solicitudes)
        # _logger.info("PRUEBA -> Se recorta a {} afilaciones".format(cantidad_afiliaciones))
        # FIN TEST

        ###################################
        ### Sincronizar cada afiliación ### Si ocurre error al crear una afiliación pasar a la siguiente
        for index, sol in enumerate(array_solicitudes):
            try:
                indice = index + 1
                _logger.info("{} de {}. {}{}".format(indice, cantidad_afiliaciones, sol['serie'], sol['contrato']))

                ### Verificar si ya existe el contrato ###
                contrato = "{}{}".format(sol['serie'], sol['contrato'])
                existe_contrato = contract_obj.search([
                    ('company_id', '=', company_id),
                    ('name', '=', contrato)
                ])

                # Si ya existe, informar a eCobro
                if existe_contrato:
                    self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], 2, "Ya existe el contrato")
                    continue

                ### Validar datos de la afiliación ###
                # 0. Obtener fecha de creación
                fecha_contrato = datetime.strptime(sol['fecha_contrato'], '%Y-%m-%d %H:%M:%S').date()

                # 1. Obtener monto de papeleria
                plan = self.env['product.pricelist.item'].search([
                    ('company_id', '=', company_id),
                    ('prefix_contract', '=', sol['serie'])
                ])

                if not plan:
                    raise ValidationError("No se encontró el plan {}".format(sol['serie']))
                if len(plan) > 1:
                    raise ValidationError("No se encontró el plan {}".format(sol['serie']))

                # 2. Calcular bono
                bonos = self.env['pabs.bonus'].search([
                    ('company_id', '=', company_id),
                    ('plan_id','=', plan.product_id.id)
                ], order = "min_value"
                )

                if not bonos:
                    raise ValidationError("No se han definido los bonos")

                inversion_inicial = float(sol['inversion_inicial'])
                bono_por_inversion = 0
                for bono in bonos:
                    if inversion_inicial >= bono.min_value and inversion_inicial <= bono.max_value:
                        bono_por_inversion = bono.bonus

                # 3. Traducir forma de pago
                forma_de_pago = "weekly"
                if sol['forma_pago'][0] in ("S","s"):
                    forma_de_pago = "weekly"
                elif sol['forma_pago'][0] in ("Q","q"):
                    forma_de_pago = "biweekly"
                elif sol['forma_pago'][0] in ("M","m"):
                    forma_de_pago = "monthly"

                # 4. Construir numero de casa con exterior e interior
                casa_num = ""
                if len(sol['domCasa_numInt']) > 0:
                    casa_num = "{} - {}".format(sol['domCasa_numExt'], sol['domCasa_numInt'])
                else:
                    casa_num = sol['domCasa_numExt']
                
                cobro_num = ""
                if len(sol['domCobro_numInt']) > 0:
                    cobro_num = "{} - {}".format(sol['domCobro_numExt'], sol['domCobro_numInt'])
                else:
                    cobro_num = sol['domCobro_numExt']

                ### Crear registros de los que depende el contrato ###
                # 1. Crear solicitud. Primero se busca la oficina del empleado
                
                #TEST. Se realiza consulta de empleado por código. En producción el id de empleado es parte de la respuesta
                employee = self.env['hr.employee'].search([
                    ('company_id', '=', company_id),
                    ('barcode', '=', sol['promotor_codigo'])
                ])
                #FIN TEST
                #employee = self.env['hr.employee'].browse(sol['promotor_id']) #PROD
                
                if not employee:
                    raise ValidationError("No se encontró al asistente")


                id_oficina = employee.warehouse_id.id
                if not id_oficina:
                    raise ValidationError("El asistente no tiene una oficina")

                id_cuenta_analitica_oficina = employee.warehouse_id.analytic_account_id.id
                if not id_cuenta_analitica_oficina:
                    raise ValidationError("La oficina no tiene una cuenta analítica asignada")

                lot_id = self.crear_solicitud(contrato, employee.id, id_oficina, plan.product_id.id, company_id)         
                if not lot_id:
                    raise ValidationError("No se pudo crear la solicitud")

                # 2. Crear partner
                partner_id = self.crear_contacto(contrato, company_id)

                if not partner_id:
                    raise ValidationError("No se pudo crear el partner")

                datos_afiliacion = {}
                
                ### Llenar datos de la afiliación. Solo debe llevar datos del modelo pabs.contract ###
                estado_civil = "sin_definir"
                if sol['afiliado_estadoCivil']:
                    estado_civil = sol['afiliado_estadoCivil']

                datos_afiliacion = {
                    'company_id': company_id,
                    'partner_id': partner_id,
                    'lot_id': lot_id,

                    'invoice_date': fecha_contrato,
                    'state': 'contract',
                    'type_view': 'precontract',
                    'captured': True,
                    'activation_code': sol['solicitud_codigoActivacion'],
                    'payment_scheme_id': 2, # Constante: comision
                    'name': contrato,
                    'sale_employee_id': employee.id, #TEST
                    #'sale_employee_id': sol['promotor_id'],
                    'contract_status_item': 21, # Constante: activo
                    'contract_status_reason': 282, # Constante: activo
                    'initial_investment': inversion_inicial,
                    'stationery': plan.stationery,
                    'comission': 0,
                    'investment_bond' : bono_por_inversion,
                    'payment_amount': sol['monto_abono'],
                    'way_to_payment': forma_de_pago,
                    'date_first_payment': sol['fecha_primer_abono'],
                    'partner_name': sol['afiliado_nombre'],
                    'partner_fname': sol['afiliado_apellidoPaterno'],
                    'partner_mname': sol['afiliado_apellidoMaterno'],
                    'birthdate': sol['afiliado_fechaNacimiento'],
                    'service_detail': 'unrealized',
                    'marital_status': estado_civil,
                    
                    # Domicilio de casa
                    'street_name': sol['domCasa_Calle'],
                    'street_number': casa_num,
                    'between_streets': sol['domCasa_EntreCalles'],
                    'municipality_id': sol['domCasa_LocalidadID'],
                    'neighborhood_id': sol['domCasa_ColoniaID'],
                    'zip_code': sol['domCasa_codigoPostal'],
                    'phone': sol['afiliado_telefono'],
                    
                    # Domicilio de cobro
                    'street_name_toll': sol['domCobro_Calle'],
                    'street_number_toll': cobro_num,
                    'between_streets_toll': sol['domCobro_entreClles'],
                    'toll_municipallity_id': sol['domCobro_LocalidadID'],
                    'toll_colony_id': sol['domCobro_ColoniaID'],
                    'zip_code_toll': sol['domCobro_codigoPostal'],
                    'phone_toll': sol['afiliado_telefono'],

                    'latitude': sol['solicitud_latitud'],
                    'longitude': sol['solicitud_longitud'],
                    'client_email': sol['afiliado_email']
                }

                ### Crear contrato con información básica ###
                contrato = contract_obj.create(datos_afiliacion)
                _logger.info("Se creó el pre contrato {}".format(contrato.id))

                ### Actualizar cuenta por cobrar del contacto. No sabemos por qué al crear el contrato se actualiza a una cuenta distinta.
                self.ActualizarCuentaContacto(partner_id)

                ### Complementar creación del contrato usando el método pabs_contract.create_contract() ###
                contrato.create_contract(vals={'lot_id' : lot_id})
                _logger.info("Se creó el contrato")

                ### Generar póliza de inversiones y excedentes ###
                id_poliza = self.CrearPoliza(company_id, fecha_contrato, contrato.name, plan.stationery, inversion_inicial - plan.stationery, id_cuenta_analitica_oficina, info_de_cuentas)

                ### Crear registro en tabla de cierre
                self.CrearRegistroPrecierre(company_id, employee.id, contrato.id, id_poliza)

                ### Actualizar en ecobro con mensaje de éxito ###
                self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], 1, "Contrato creado")

            except Exception as ex:
                _logger.error("Error al procesar: {}".format(ex))
                self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], 0, "{}".format(ex)[0:248])
                continue            

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def crear_contacto(self, contrato, company_id):
        _logger.info("Comienza creación de partner")

        partner_obj = self.env['res.partner']
        account_obj = self.env['account.account']

        ### Validar datos ###
        if not contrato:
            raise ValidationError("No se asignó un número de contrato")
        
        if not company_id:
            raise ValidationError("No se asignó un id de compañia")

        ### Buscar cuentas contables ###
        cuenta_a_cobrar = account_obj.search([('company_id','=',company_id), ('code','=','110.01.002')]) #Afiliaciones plan previsión electrónicos
        cuenta_a_pagar = account_obj.search([('company_id','=',company_id), ('code','=','201.01.001')]) #Proveedores nacionales

        if not cuenta_a_cobrar:
            raise ValidationError("No se encontró la cuenta 110.01.002 - Afiliaciones plan previsión electronicos")

        if not cuenta_a_pagar:
            raise ValidationError("No se encontró la cuenta 201.01.001 - Proveedores nacionales")

        ### Buscar un partner con el mismo nombre###
        partner = partner_obj.search([
            ('company_id', '=', company_id),
            ('name', '=', contrato)
        ])

        ### Si ya existe un partner actualizar las cuentas. Si no existe, crear ###
        if partner:
            _logger.info("Ya existe partner -> {}. Se actualizan cuentas contables".format(partner.id))
            partner.write({"property_account_receivable_id": cuenta_a_cobrar.id, "property_account_payable_id": cuenta_a_pagar.id})
            return partner.id
        else: 
            data = {
            'company_type': 'person',
            'name': contrato,
            'property_account_receivable_id': cuenta_a_cobrar.id, 
            'property_account_payable_id': cuenta_a_pagar.id,
            'company_id': company_id
            }

            new_partner_id = partner_obj.create(data)

            _logger.info("Se creó partner: {}".format(new_partner_id.id))
            return new_partner_id.id

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    
    ### Se creó este método para compensar un proceso desconocido: al llamar model.create() actualiza la cuenta del contacto a la cuenta '110.01.001'
    def ActualizarCuentaContacto(self, partner_id):        
        # Buscar partner
        partner = self.env['res.partner'].browse(partner_id)

        if not partner:
            raise ValidationError("No se encontró un partner")

        ### Buscar cuentas contables ###
        cuenta_a_cobrar = self.env['account.account'].search([('company_id','=', partner.company_id.id), ('code','=','110.01.002')]) #Afiliaciones plan previsión electrónicos

        if not cuenta_a_cobrar:
            raise ValidationError("No se encontró la cuenta 110.01.002 - Afiliaciones plan previsión electronicos")

        partner.write({'property_account_receivable_id': cuenta_a_cobrar.id})

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def crear_solicitud(self, contrato, employee_id, warehouse_id, product_id, company_id):
        _logger.info("Comienza creación de solicitud")

        stock_obj = self.env['stock.production.lot']

        # Validar datos
        if not contrato:
            raise ValidationError("No se asignó un número de contrato")

        if not employee_id:
            raise ValidationError("No se asignó un id de empleado")
        
        if not company_id:
            raise ValidationError("No se asignó un id de compañia")

        #Buscar si ya existe la solicitud
        lot = stock_obj.search([
            ('company_id', '=', company_id),
            ('name', '=', contrato)
        ])

        #Si ya existe la solicitud regresar. Si no existe, crear.
        if lot:
            _logger.info("Ya existe solicitud {}. Se actualiza empleado y oficina".format(lot.id))
            lot.write({'employee_id': employee_id, 'warehouse_id': warehouse_id})
            return lot.id
        else:
            datos_solicitud = {
                'company_id': company_id,
                'name': contrato,
                'product_id': product_id,
                'product_uom_id': 1,
                'active': True,
                'employee_id': employee_id,
                'warehouse_id': warehouse_id 
            }

            new_lot_id = stock_obj.create(datos_solicitud)
            _logger.info("Se creó solicitud: {}".format(new_lot_id.id))
            return new_lot_id.id

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    # Actualiza el estatus de captura de la solicitud en ecobro
    # 2 = Ya existe el contrato
    # 1 = Creado
    # 0 = No creado
    def ActualizarAfiliacionEnEcobro(self, url, id_contrato, registro, mensaje):
        try:
            _logger.info("Actualizando en eCobro: {},{},{}".format(id_contrato, registro, mensaje))
            data_response = {"contratos" : [
                {
                    "contrato_id": id_contrato,
                    "registrada": registro,
                    "resultado": mensaje
                }
            ]}

            llamada = requests.post(url, json=data_response)
            
            respuesta = json.loads(llamada.text)

            if len(respuesta['success']) > 0:
                _logger.info("Actualizada en eCobro")
            else:
                _logger.warning("No actualizada")
        except Exception as ex:
            mensaje = "Error al actualizar por web service: {}".format(ex)
            _logger.error(mensaje)
            raise ValidationError(mensaje)

#################################################################################################################################################
######################################                  GENERACIÓN DE POLIZAS             #######################################################
#################################################################################################################################################

    def ValidarCuentas(self, company_id, info_de_cuentas):
        try:
            company = self.env['res.company'].browse(company_id)

            id_cuenta_debito = self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('code', '=', CUENTA_TRANSITO)
            ]).id

            if not id_cuenta_debito:
                _logger.error("No se encontró la cuenta contable {} - {}".format(CUENTA_TRANSITO, NOMBRE_CUENTA))
                return False

            id_cuenta_credito_inversiones = company.initial_investment_account_id.id
            if not id_cuenta_credito_inversiones:
                _logger.error("No se encontró la cuenta contable de inversiones iniciales")
                return False

            id_cuenta_credito_excedentes = company.excedent_account_id.id
            if not id_cuenta_credito_excedentes:
                _logger.error("No se encontró la cuenta contable de excedentes")
                return False

            journal_id = company.account_journal_id.id
            if not journal_id:
                _logger.error("No se encontró el diario configurado para la póliza de inversiones y excedentes")
                return False

            info_de_cuentas = {
                'id_cuenta_debito': id_cuenta_debito,
                'id_cuenta_credito_inversiones': id_cuenta_credito_inversiones,
                'id_cuenta_credito_excedentes': id_cuenta_credito_excedentes,
                'journal_id': journal_id
            }

            return info_de_cuentas
        except Exception as ex:
            _logger.error("Error al validar cuentas {}".format(ex))
            return {}

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    
    def CrearPoliza(self, company_id, fecha, numero_contrato, papeleria, excedente, id_cuenta_analitica_almacen, info_de_cuentas):
        _logger.info("Comienza creación de póliza")
        
        move_obj = self.env['account.move']

        company = self.env['res.company'].browse(company_id)

        ### Validar que no exista una poliza anterior ###
        existe_poliza = move_obj.search([
            ('company_id', '=', company.id),
            ('ref', '=', numero_contrato)
        ])

        if existe_poliza:
            raise ValidationError("Ya existe la poliza")

        apuntes = []

        ### Creación de póliza ###
        # Si es fiscal
        if company.apply_taxes:
            # Buscar impuesto de IVA
            impuesto_IVA = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', company.id)])
            if not impuesto_IVA:
                raise ValidationError("No se encontró el impuesto con nombre IVA")

            # Buscar contra cuenta de IVA
            if not impuesto_IVA.inverse_tax_account:
                raise ValidationError("No se ha definido la contra cuenta de IVA en el impuesto IVA")

            factor_iva = 1 + (impuesto_IVA.amount / 100)

            #Linea de Inversiones iniciales
            monto_inversion = papeleria
            apuntes.append([0,0,{
                'account_id' : info_de_cuentas['id_cuenta_credito_inversiones'],
                'name' : numero_contrato,
                'debit' : 0,
                'credit' : round( monto_inversion / factor_iva, 2),
                'analytic_account_id' : id_cuenta_analitica_almacen or False,
            }])

            #Linea de Excedentes
            monto_excedente = excedente

            if monto_excedente > 0:
                apuntes.append([0,0,{
                    'account_id' : info_de_cuentas['id_cuenta_credito_excedentes'],
                    'name' : numero_contrato,
                    'debit' : 0,
                    'credit' : round( monto_excedente / factor_iva, 2),
                    'analytic_account_id' : id_cuenta_analitica_almacen or False,
                }])

            #Linea de IVA (Una linea sumando inversiones y excedentes)
            apuntes.append([0,0,{
                'account_id' : impuesto_IVA.inverse_tax_account.id,
                'name' : "IVA",
                'debit' : 0,
                'credit' : round( (monto_inversion + monto_excedente) - (round( monto_inversion / factor_iva, 2) + round( monto_excedente / factor_iva, 2)), 2),
                'tax_ids' : [(4, impuesto_IVA.id, 0)],
            }])
        # No fiscal
        else:
            ### INVERSIONES INICIALES
            apuntes.append([0,0,{
                'account_id' : info_de_cuentas['id_cuenta_credito_inversiones'],
                'name' : numero_contrato,
                'debit' : 0,
                'credit' : papeleria,
                'analytic_account_id' : id_cuenta_analitica_almacen or False,
            }])
            ### EXCEDENTES
            if excedente > 0:
                apuntes.append([0,0,{
                    'account_id' : info_de_cuentas['id_cuenta_credito_excedentes'],
                    'name' : numero_contrato,
                    'debit' : 0,
                    'credit' : excedente,
                    'analytic_account_id' : id_cuenta_analitica_almacen or False,
                }])

        ### Linea de Caja transito
        apuntes.append([0,0,{
            'account_id' : info_de_cuentas['id_cuenta_debito'],
            'name' : numero_contrato,
            'debit' : papeleria + excedente,
            'credit' : 0
        }])

        asiento = {
            'ref' : numero_contrato,
            'date' : fecha,
            'journal_id' : info_de_cuentas['journal_id'],
            'company_id' : company.id,
            'line_ids' : apuntes
        }

        # Crear póliza
        move_id = move_obj.create(asiento)
        _logger.info("Se creó la póliza")
        
        # Validar póliza
        move_id.action_post()
        _logger.info("Se validó la póliza")

        return move_id.id

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def CrearRegistroPrecierre(self, company_id, id_asistente, id_contrato, id_poliza_caja_transito):
        _logger.info("Comienza registro de precierre")

        obj_cierre = self.env['pabs.econtract.move']

        #Buscar que no exista registro
        existe_cierre = obj_cierre.search([
            ('company_id', '=', company_id),
            ('id_asistente', '=', id_asistente),
            ('id_contrato', '=', id_contrato),
            ('id_poliza_caja_transito', '=', id_poliza_caja_transito)
        ])

        if existe_cierre:
            _logger.warning("Ya existe registro de precierre id_contrato {}".format(id_contrato))
            return

        datos = {
            'company_id': company_id,
            'id_asistente': id_asistente,
            'id_contrato': id_contrato,
            'id_poliza_caja_transito': id_poliza_caja_transito,
            'estatus': 'sin_cierre'
        }

        obj_cierre.create(datos)

        _logger.info("Se crea registro de precierre")

#################################################################################################################################################
######################################                SINCRONIZADOR DE CORTES             #######################################################
#################################################################################################################################################

    def SincronizarCortes(self, company_id):
        _logger.info("Comienza sincronización de cortes")

        if not company_id:
            raise ValidationError("No se ha definido una compañia")

        ### Validar web service de consulta y respuesta ###
        url_obtener_cortes = self.get_url(company_id, 3)
        if not url_obtener_cortes:
            _logger.error("No se ha definido la dirección del web service: obtener cortes")
            return

        url_actualizar_corte = self.get_url(company_id, 4)
        if not url_actualizar_corte:
            _logger.error("No se ha definido la dirección del web service: actualizar cortes")
            return

        ### Llamar web service de consulta ###
        try:
            _logger.info("Comienza consulta de cortes")
            respuesta = requests.post(url_obtener_cortes)
            json_cortes = json.loads(respuesta.text)
            array_cortes = json_cortes.get('result')
        except Exception as ex:
            _logger.error("Error al consultar los cortes de afiliaciones electrónicas {}".format(ex))
            return

        cantidad_cortes = len(array_cortes)
        _logger.info("Cortes obtenidos: {}".format(cantidad_cortes))

        corte_obj = self.env['pabs.econtract.move']
        ### Actualizar registros de corte ###
        cantidad_cortes
        for index, cor in enumerate(array_cortes):
            try:
                _logger.info("{} de {}. {}".format(index + 1, cantidad_cortes, cor['contrato']))

                ### Buscar registro de corte
                corte = corte_obj.search([
                    ('company_id', '=', company_id),
                    ('id_contrato.name', '=', cor['contrato'])
                ])

                if not corte:
                    _logger.error("No se encontró el corte")
                    continue

                if len(corte) > 1:
                    raise ValidationError("Se encontró más de un corte")

                if corte.estatus == 'cerrado':
                    _logger.warning("Ya existe el registro de corte")
                    self.ActualizarCorteEnEcobro(url_actualizar_corte, cor['id'])
                    continue

                if corte.estatus == 'confirmado':
                    _logger.warning("Ya fue recibida en contratos")
                    self.ActualizarCorteEnEcobro(url_actualizar_corte, cor['id'])
                    continue
                
                ### Actualizar en odoo ###
                corte.write({
                    'periodo': cor['periodo'],
                    'fecha_hora_cierre': cor['fecha_cierre_periodo'],
                    'estatus': 'cerrado'
                })

                _logger.info("Actualizado en odoo")

                ### Actualizar en eCobro ###
                self.ActualizarCorteEnEcobro(url_actualizar_corte, cor['id'])

            except Exception as ex:
                mensaje = "Error al procesar corte: {}".format(ex)
                _logger.error(mensaje)

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    
    def ActualizarCorteEnEcobro(self, url_actualizar_corte, id_contrato):
        data_response = {"result": [id_contrato]}

        llamada = requests.post(url_actualizar_corte, json=data_response)
        
        respuesta = json.loads(llamada.text)

        if respuesta['result'] == True:
            _logger.info("Actualizada en eCobro")
        else:
            _logger.warning("No actualizada")

#################################################################################################################################################
######################################           SINCRONIZACION DE COBRADORES ASIGNADOS        ##################################################
#################################################################################################################################################

    def SincronizarCobradoresAsignados(self, company_id):

        _logger.info("Comienza sincronización de cobradores asignados a contratos")

        contract_obj = self.env['pabs.contract']

        ### Validar parámetros ###
        if not company_id:
            _logger.error("No se ha definido la compañia")
            return

        ### Validar web service de consulta y respuesta ###
        url_obtener_contratos = self.get_url(company_id, 5)
        if not url_obtener_contratos:
            _logger.error("No se ha definido la dirección del web service: obtener cobradores asignados")
            return

        url_actualizar_contratos = self.get_url(company_id, 6)
        if not url_actualizar_contratos:
            _logger.error("No se ha definido la dirección del web service: actualizar contratos con cobrador asignado")
            return

        ### Llamar web service de consulta ###
        try:
            _logger.info("Comienza consulta de cobradores")
            respuesta = requests.post(url_obtener_contratos)
            json_contratos = json.loads(respuesta.text)
            array_contratos = json_contratos.get('result')
        except Exception as ex:
            _logger.error("Error al consultar cobradores {}".format(ex))
            return

        cantidad_contratos = len(array_contratos)
        _logger.info("Contratos obtenidos: {}".format(cantidad_contratos))

        ### Llenar lista de cobradores ###
        lista_cobradores = []
        cobradores = self.env['hr.employee'].search([
            ('company_id', '=', company_id),
            ('job_id.name', 'ilike', 'COBRA')
        ])

        for cob in cobradores:
            lista_cobradores.append({
                'id_cobrador': cob.id,
                'codigo': cob.barcode
            })

        if not lista_cobradores:
            raise ValidationError("No hay empleados con el cargo COBRADOR")

        # TEST
        # for i in range(1, cantidad_contratos): # Tomar solo X elementos de la lista
        #     array_contratos.pop(1)
        # cantidad_contratos = len(array_contratos)
        # _logger.info("PRUEBA -> Se recorta a {} contratos".format(cantidad_contratos))
        # FIN TEST

        ###################################
        ### Sincronizar cada contrato ### Si ocurre error al actualizar un contrato pasar al siguiente
        for index, con in enumerate(array_contratos):
            try:
                indice = index + 1
                
                #con['contrato'] = "2DJ000026"#TEST
                #con['no_cobrador'] = 50835 #TEST
                
                _logger.info("{} de {}. {} -> {}".format(indice, cantidad_contratos, con['contrato'], con['codigo']))

                ### Buscar cobrador en lista de cobradores
                cobrador = list(filter(lambda x: x['codigo'] == con['codigo'], lista_cobradores))

                if not cobrador:
                    raise ValidationError("No se encontró al cobrador")

                ### Actualizar contrato ###
                contrato = contract_obj.search([
                    ('company_id', '=', company_id),
                    ('name', '=', con['contrato'])
                ])

                if not contrato:
                    raise ValidationError("No se encontró el contrato")

                contrato.write({
                    'debt_collector': con['no_cobrador'],
                    'assign_collector_date': fields.Date.today()
                })

                _logger.info("Actualizado en Odoo")
     
                self.ActualizarAsignacionEnEcobro(url_actualizar_contratos, con['ContratosAsignados_ContratoAsignadoID'])  

            except Exception as ex:
                _logger.error("Error al actualizar contrato: {}".format(ex))

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    
    def ActualizarAsignacionEnEcobro(self, url_actualizar_asignacion, id_asignacion):
        data_response = {"id": id_asignacion}

        llamada = requests.post(url_actualizar_asignacion, json=data_response)
        
        respuesta = json.loads(llamada.text)

        if respuesta['result'] == "Contrato actualizado":
            _logger.info("Actualizado en eCobro")
        else:
            raise ValidationError("No actualizada en eCobro")