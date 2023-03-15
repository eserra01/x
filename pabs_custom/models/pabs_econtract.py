# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import pytz

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

### Sincronizadores a crear ###
# 1. Sincronizador de afiliaciones
# 2. Sincronizador de cortes
# 3. Sincronizador de cobradores asignados
# 4. Sincronizador de direcciones

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
                elif tipo in (7,8):
                    plaza_ecobro = "ecobrosalt"
                else:
                    plaza_ecobro = "asistencia_social_SLW"

            if company_id == 16:
                if tipo in (5,6):
                    plaza_ecobro = "ecobroSAP_TAM"
                elif tipo in (7,8):
                    plaza_ecobro = ""
                else:
                    plaza_ecobro = ""

            if company_id == 8:
                if tipo in (5,6):
                    plaza_ecobro = "ecobroSAP_VSA"
                elif tipo in (7,8):
                    plaza_ecobro = ""
                else:
                    plaza_ecobro = ""
                    
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
            # Sincronizar cortes
            elif tipo == 3:
                metodo = "controlsolicitudes/getContractsNotSynced"
            elif tipo == 4:
                metodo = "controlsolicitudes/updateContractsNotSynced"
            # Sincronizar cobradores asignados
            elif tipo == 5:
                metodo = "controlmapa/getContractsAssigned"
            elif tipo == 6:
                metodo = "controlmapa/updateContractsAssignedasSync"
            # Sincronizar direcciones actualizadas
            elif tipo == 7:
                metodo = "controlcartera/getNewClientInfoRegistered"
            elif tipo == 8:
                metodo = "controlcartera/updateClienteDetalleAsUpdated"
            # Sincronizar datos de afiliacion
            elif tipo == 9:
                metodo = "controlsolicitudes/getClientInfoUpdated"
            elif tipo == 10:
                metodo = "controlsolicitudes/setClientInfoUpdatedAsSync"

            if not metodo:
                _logger.error("No se ha definido la plaza de ecobro")
                raise ValidationError("No se ha definido el método a llamar")
            
            return "http://{}/{}/{}".format(direccion_ip, plaza_ecobro, metodo)
        except Exception as ex:
            _logger.error("Error al consultar url {}")
            return ""

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def SincronizarContratos(self, company_id, solicitud):
        _logger.info("Comienza sincronización de afiliaciones electrónicas compañia: {}".format(company_id))

        contract_obj = self.env['pabs.contract']
        municipality_obj = self.env['res.locality']
        colonia_obj = self.env['colonias']

        url_obtener_afiliaciones = ""
        url_actualizar_afiliaciones = ""
        array_solicitudes = []

        if solicitud:
            # TEST
            # solicitud = {
            #     "qr_string": "202205231256513DJ000183MC340568525.3852089-101.0111063",
            #     "contrato_id": "999999",
            #     "serie": "PCD",
            #     "contrato": "000006",
            #     "solicitud_codigoActivacion": "MC0000006",
            #     "inversion_inicial": "500",
            #     "fecha_contrato": "2022-09-28 12:56:51",
            #     "timestamp": "1653332211",
            #     "fecha_primer_abono": "2022-11-01",
            #     "monto_abono": "400",
            #     "forma_pago": "Mensuales",
            #     "promotor_id": "260",
            #     "promotor_nombre": "FELIPE ANGELES RAMOS ALMANZA1",
            #     "promotor_codigo": "P0251",
            #     "plan_id": "2076",
            #     "plan": "IMPERIAL PREMIUM",
            #     "solicitud_latitud": "25.3852089",
            #     "solicitud_longitud": "-101.0111063",
            #     "afiliado_nombre": "MARÍA DEL ROBLE",
            #     "afiliado_apellidoPaterno": "JUAREZ",
            #     "afiliado_apellidoMaterno": "RAMIREZ",
            #     "afiliado_fechaNacimiento": "1973-03-10",
            #     "afiliado_estadoCivil": "",
            #     "afiliado_ocupacion": "",
            #     "afiliado_telefono": "8442568280",
            #     "afiliado_RFC": " ",
            #     "afiliado_email": "roblejr73@gmail.com",
            #     "tipo_domicilio": "Casa",
            #     "domCasa_codigoPostal": "25086",
            #     "domCasa_Calle": "ABEL BARRAGAN",
            #     "domCasa_numExt": "251",
            #     "domCasa_numInt": "",
            #     "domCasa_EntreCalles": "FRANCISCO H GARZA Y BOULEVARD CID GONZALEZ",
            #     "domCasa_Colonia": "BUROCRATAS MUNICIPALES",
            #     "domCasa_Municipio": "SALTILLO",
            #     "domCasa_LocalidadID": "99998",
            #     "domCasa_ColoniaID": "99998",
            #     "domCobro_tipoDomicilio": "Cobranza",
            #     "domCobro_codigoPostal": "25086",
            #     "domCobro_Calle": "ABEL BARRAGAN",
            #     "domCobro_numExt": "251",
            #     "domCobro_numInt": "",
            #     "domCobro_entreClles": "FRANCISCO H GARZA Y BOULEVARD CID GONZALEZ",
            #     "domCobro_Colonia": "BUROCRATAS MUNICIPALES",
            #     "domCobro_Municipio": "SALTILLO",
            #     "domCobro_LocalidadID": "99998",
            #     "domCobro_ColoniaID": "99998",
            #     "generar_contrato": "0"
            # }

            array_solicitudes.append(solicitud)
        else:
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
        _logger.info("{} >>> Afiliaciones electrónicas a sincronizar: {}".format(company_id, cantidad_afiliaciones))

        # TEST
        # for i in range(1, cantidad_afiliaciones): # Tomar solo X elementos de la lista
        #     array_solicitudes.pop(1)
        # cantidad_afiliaciones = len(array_solicitudes)
        # _logger.info("PRUEBA -> Se recorta a {} afilaciones".format(cantidad_afiliaciones))

        ###################################
        ### Sincronizar cada afiliación ### Si ocurre error al crear una afiliación pasar a la siguiente
        for index, sol in enumerate(array_solicitudes):
            try:
                indice = index + 1
                _logger.info("{} de {}. {}{}".format(indice, cantidad_afiliaciones, sol['serie'], sol['contrato']))

                pre_numero_contrato = "{}{}".format(sol['serie'], sol['contrato'])
                generar_contrato = sol['generar_contrato']
                
                ### Verificar si ya existe el pre contrato ###
                if generar_contrato == "0":
                    contrato = contract_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', pre_numero_contrato)
                    ])

                    if contrato:
                        msj = "Ya existe el pre-contrato"
                        _logger.info(msj)

                        if solicitud:
                            return {"resultado": 1, "msj": "{} - {}".format(msj, pre_numero_contrato)}
                        else:
                            self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], generar_contrato, "", "", 1, msj)
                        continue

                ### Si se debe generar contrato obtener siguiente número de contrato y asignar al contrato y al contacto. Si ya existe responder. ###
                if generar_contrato == "1":
                    contrato = contract_obj.search([
                        ('company_id', '=', company_id),
                        ('lot_id.name', '=', pre_numero_contrato)
                    ])

                    if not contrato:
                        msj = "No se encontró el pre-contrato"
                        _logger.info(msj)

                        if solicitud:
                            return {"resultado": 0, "msj": "{} - {}".format(msj, pre_numero_contrato)}
                        else:
                            self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], generar_contrato, sol['serie'], sol['contrato'], 0, msj)
                    elif contrato.state == "contract": #singleton cuando hay dos contratos con mismo número de solicitud
                        msj = "El contrato ya habia sido creado"
                        _logger.info(msj)

                        if solicitud:
                            return {"resultado": 1, "msj": "{} - {}".format(msj, pre_numero_contrato)}
                        else:
                            self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], generar_contrato, contrato.name[0:3], contrato.name[3:], 1, msj)
                    else:
                        # Se busca la tarifa porque esta ligada a la secuencia
                        tarifa = self.env['product.pricelist.item'].search([('product_id', '=', contrato.name_service.id)])
                        if not tarifa:
                            raise ValidationError(("No se encontró la información del plan {}".format(contrato.product_id.name)))

                        siguiente_numero = tarifa.sequence_id._next()
                        contrato.write({'name': siguiente_numero, 'state': 'contract'})
                        contrato.partner_id.write({'name' : siguiente_numero})
                        
                        msj = "Se asignó número de contrato {}".format(contrato.name)
                        _logger.info(msj)

                        if solicitud:
                            return {"resultado": 1, "msj": "{} - {}".format(msj, pre_numero_contrato)}
                        else:
                            self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], generar_contrato, siguiente_numero[0:3], siguiente_numero[3:99], 1, msj)
                        
                    continue

                ### Validar datos de la afiliación ###
                # 0. Obtener fecha de creación
                fecha_contrato = datetime.strptime(sol['fecha_contrato'], '%Y-%m-%d %H:%M:%S').date()

                # 1. Obtener monto de papeleria
                plan = self.env['product.pricelist.item'].search([
                    ('company_id', '=', company_id),
                    ('product_tmpl_id', '=', int(sol['plan_id']))
                ])

                if not plan:
                    raise ValidationError("No se encontró el plan {}".format(sol['plan']))
                if len(plan) > 1:
                    raise ValidationError("No se encontró el plan {}".format(sol['plan']))

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

                # 5. Obtener id de municipio y colonia
                id_municipio = 0
                id_colonia = 0
                id_municipio_cobro = 0
                id_colonia_cobro = 0
                
                # 5.1 Municipio casa
                if sol['domCasa_Municipio']:
                    nombre = sol['domCasa_Municipio']
                    municipio = municipality_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre)
                    ], limit = 1)

                    # Si no existe el municipio, crearlo. Tomar los otros datos del primer registro
                    if not municipio:
                        mun = municipality_obj.search([('company_id', '=', company_id)], limit = 1)

                        if not mun:
                            raise ValidationError("No existen municipios")

                        id_municipio = municipality_obj.create({
                            'name': nombre,
                            'country_id': mun.country_id.id,
                            'state_id': mun.state_id.id,
                            'company_id': company_id
                        }).id

                        _logger.info("Se crea municipio de casa {}".format(nombre))
                    else:
                        id_municipio = municipio.id

                if id_municipio == 0:
                    raise ValidationError("No se pudo obtener el municipio de casa")

                # 5.2 Municipio cobro
                if sol['domCobro_Municipio']:
                    nombre = sol['domCobro_Municipio']
                    municipio = municipality_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre)
                    ], limit = 1)

                    # Si no existe el municipio, crearlo. Tomar los otros datos del primer registro
                    if not municipio:
                        mun = municipality_obj.search([('company_id', '=', company_id)], limit = 1)

                        if not mun:
                            raise ValidationError("No existen municipios")

                        id_municipio_cobro = municipality_obj.create({
                            'name': nombre,
                            'country_id': mun.country_id.id,
                            'state_id': mun.state_id.id,
                            'company_id': company_id
                        }).id

                        _logger.info("Se crea municipio de cobro {}".format(nombre))
                    else:
                        id_municipio_cobro = municipio.id
                
                if id_municipio_cobro == 0:
                    raise ValidationError("No se pudo obtener el municipio de cobro")

                # 5.3 Colonia casa
                if sol['domCasa_Colonia']:
                    nombre = sol['domCasa_Colonia']
                    colonia = colonia_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre),
                        ('municipality_id', '=', id_municipio)
                    ], limit = 1)

                    # Si no existe la colonia, crearla
                    if not sol['domCasa_codigoPostal']:
                        raise ValidationError("No se encontró el codigo postal de la colonia de casa")

                    if not colonia:
                        id_colonia = colonia_obj.create({
                            'name': nombre,
                            'municipality_id': id_municipio,
                            'company_id': company_id,
                            'zip_code': sol['domCasa_codigoPostal']
                        }).id

                        _logger.info("Se crea colonia de casa {}".format(nombre))
                    else:
                        id_colonia = colonia.id

                if id_colonia == 0:
                    raise ValidationError("No se pudo obtener la colonia de casa")
                
                # 5.4 Colonia cobro
                if sol['domCobro_Colonia']:
                    nombre = sol['domCobro_Colonia']
                    colonia = colonia_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre),
                        ('municipality_id', '=', id_municipio_cobro)
                    ], limit = 1)

                    # Si no existe la colonia, crearla
                    if not sol['domCobro_codigoPostal']:
                        raise ValidationError("No se encontró el codigo postal de la colonia de cobro")

                    if not colonia:
                        id_colonia_cobro = colonia_obj.create({
                            'name': nombre,
                            'municipality_id': id_municipio,
                            'company_id': company_id,
                            'zip_code': sol['domCobro_codigoPostal']
                        }).id

                        _logger.info("Se crea colonia de cobro {}".format(nombre))
                    else:
                        id_colonia_cobro = colonia.id

                if id_colonia_cobro == 0:
                    raise ValidationError("No se pudo obtener la colonia de cobro")

                ### Crear registros de los que depende el contrato ###
                # 1. Crear solicitud. Primero se busca la oficina del empleado
                
                employee = self.env['hr.employee'].search([
                    ('company_id', '=', company_id),
                    ('barcode', '=', sol['promotor_codigo'])
                ])
                
                if not employee:
                    raise ValidationError("No se encontró al asistente")

                id_oficina = employee.warehouse_id.id
                if not id_oficina:
                    raise ValidationError("El asistente no tiene una oficina")

                id_cuenta_analitica_oficina = employee.warehouse_id.analytic_account_id.id
                if not id_cuenta_analitica_oficina:
                    raise ValidationError("La oficina no tiene una cuenta analítica asignada")

                lot_id = self.crear_solicitud(pre_numero_contrato, employee.id, id_oficina, plan.product_id.id, company_id)
                if not lot_id:
                    raise ValidationError("No se pudo crear la solicitud")

                # 2. Crear partner
                partner_id = self.crear_contacto(pre_numero_contrato, company_id)

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
                    'qr_string': sol['qr_string'],
                    'state': 'precontract',
                    'type_view': 'precontract',
                    'captured': True,
                    'activation_code': sol['solicitud_codigoActivacion'],
                    'payment_scheme_id': 2, # Constante: comision
                    'name': pre_numero_contrato,
                    'sale_employee_id': employee.id,
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
                    'municipality_id': id_municipio,
                    'neighborhood_id': id_colonia,
                    'zip_code': sol['domCasa_codigoPostal'],
                    'phone': sol['afiliado_telefono'],
                    
                    # Domicilio de cobro
                    'street_name_toll': sol['domCobro_Calle'],
                    'street_number_toll': cobro_num,
                    'between_streets_toll': sol['domCobro_entreClles'],
                    'toll_municipallity_id': id_municipio_cobro,
                    'toll_colony_id': id_colonia_cobro,
                    'zip_code_toll': sol['domCobro_codigoPostal'],
                    'phone_toll': sol['afiliado_telefono'],

                    'latitude': sol['solicitud_latitud'],
                    'longitude': sol['solicitud_longitud'],
                    'client_email': sol['afiliado_email']
                }

                ### Crear contrato con información básica ###
                contrato = contract_obj.create(datos_afiliacion)
                _logger.info("Se creó el precontrato con id: {}".format(contrato.id))

                ### Actualizar cuenta por cobrar del contacto. No sabemos por qué al crear el contrato se actualiza a una cuenta distinta.
                self.ActualizarCuentaContacto(partner_id)

                ### Crear registro en tabla de cierre
                self.CrearRegistroPrecierre(company_id, employee.id, contrato.id)

                ### Actualizar en ecobro con mensaje de éxito ###
                msj = "Precontrato creado"
                _logger.info(msj)

                if solicitud:
                    return {"resultado": 1, "msj": "{} - {}".format(msj, pre_numero_contrato)}
                else:
                    self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], generar_contrato, "", "", 1, msj)

            except Exception as ex:
                msj = "Error al procesar: {}".format(ex)
                _logger.error(msj)

                if solicitud:
                    return {"resultado": 0, "msj": msj[0:248]}
                else:
                    self.ActualizarAfiliacionEnEcobro(url_actualizar_afiliaciones, sol['contrato_id'], generar_contrato, "", "", 0, "{}".format(ex)[0:248])

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
    # Registrada: 0 = No creado; 1 = Creado; 2 = Ya existe el contrato
    def ActualizarAfiliacionEnEcobro(self, url, id_contrato, generar_contrato, serie, contrato, registrada, mensaje):

        try:
            _logger.info("Actualizando en eCobro: {},{},{}".format(id_contrato, registrada, mensaje))
            data_response = {"contratos" : [
                {
                    "contrato_id": id_contrato,
                    "generar_contrato": generar_contrato,
                    "serie": serie,
                    "contrato": contrato,
                    "registrada": registrada,
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
######################################          ACTUALIZAR DATOS DE SOLICITUDES           #######################################################
#################################################################################################################################################

    #Actualiza los datos de la afiliación electrónica con los cambios hechos desde la aplicación
    def ActualizarDatosDeAfiliaciones(self, company_id, solicitud):
        _logger.info("Comienza actualización de datos de afiliaciones electrónicas")

        contract_obj = self.env['pabs.contract']
        municipality_obj = self.env['res.locality']
        colonia_obj = self.env['colonias']

        array_afiliaciones = []
        url_consultar_actualizaciones = ""
        url_consultar_actualizaciones = ""
        
        if solicitud:
            array_afiliaciones.append(solicitud)
        else:
            ### Obtener web services ###
            url_consultar_actualizaciones = self.get_url(company_id, 9)
            url_actualizar_afiliaciones = self.get_url(company_id, 10)

            if not url_consultar_actualizaciones or not url_actualizar_afiliaciones:
                _logger.error("No se han definido los web service de consulta y actualización")
                return

            try:
                respuesta = requests.post(url_consultar_actualizaciones)
                json_afiliaciones = json.loads(respuesta.text) # NO ES TEST
                array_afiliaciones = json_afiliaciones.get('solicitudes')
            except Exception as ex:
                _logger.error("Error al consultar las afiliaciones por actualizar {}".format(ex))
                return

            if not array_afiliaciones:
                _logger.info("No hay afiliaciones por actualizar")
                return
            
            #TEST#
            # json_afiliaciones = {
            #     "solicitudes": [
            #         {
            #             "serie": "3NJ",
            #             "contrato": "000019",
                        
            #             "afiliado_nombre": "HUGO",
            #             "afiliado_apellidoPaterno": "JURADO",
            #             "afiliado_apellidoMaterno": "MUSTANG",
            #             "afiliado_fechaNacimiento": "1957-11-17",
            #             "afiliado_telefono": "2580963741",
            #             "afiliado_email": "corre@correo.com",

            #             "tipo_domicilio": "Casa",
            #             "domCasa_codigoPostal": "25204",
            #             "domCasa_Calle": "Casonas",
            #             "domCasa_numExt": "123",
            #             "domCasa_numInt": "",
            #             "domCasa_EntreCalles": "Entre calles casa",
            #             "domCasa_Colonia": "ALBAREDA RESIDENCIAL 3",
            #             "domCasa_Municipio": "SALTILLO",
            #             "domCasa_LocalidadID": "37151",
            #             "domCasa_ColoniaID": "37151",

            #             "domCobro_tipoDomicilio": "Cobranza",
            #             "domCobro_codigoPostal": "25204",
            #             "domCobro_Calle": "Cobronas",
            #             "domCobro_numExt": "456",
            #             "domCobro_numInt": "",
            #             "domCobro_entreClles": "Entre calles cobro",
            #             "domCobro_Colonia": "BONANZA",
            #             "domCobro_Municipio": "SALTILLO",
            #             "domCobro_LocalidadID": "37151",
            #             "domCobro_ColoniaID": "37151",

            #             "qr_string": "20220714144639ASD000073MC761158820.6823975-103.3816011",
            #             "contrato_id": "531",
            #             "solicitud_codigoActivacion": "MC7611588",
            #             "inversion_inicial": "500",
            #             "fecha_contrato": "2022-07-14 14:46:39",
            #             "timestamp": "1657827999",
            #             "fecha_primer_abono": "2022-07-21",
            #             "monto_abono": "300",
            #             "forma_pago": "Mensuales",
            #             "promotor_id": "712",
            #             "promotor_nombre": "VENTAS OFICINA X",
            #             "promotor_codigo": "P9999",
            #             "plan_id": "2076",
            #             "plan": "IMPERIAL PREMIUM",
            #             "solicitud_latitud": "20.6823975",
            #             "solicitud_longitud": "-103.3816011",
            #             "afiliado_estadoCivil": "",
            #             "afiliado_ocupacion": "",
            #             "afiliado_RFC": " "
            #         }
            #     ]
            # }

        ### Iterar en cada afiliacion ###
        cantidad_afiliaciones = len(array_afiliaciones)
        for index, afi in enumerate(array_afiliaciones, 1):
            try:
                numero_de_contrato = "{}{}".format(afi['serie'], afi['contrato'])
                _logger.info("{} de {}. {}".format(index, cantidad_afiliaciones, numero_de_contrato))

                ### Buscar contrato ###
                contrato = contract_obj.search([
                    ('company_id', '=', company_id),
                    '|', ('name', '=', numero_de_contrato),
                    ('lot_id.name', '=', numero_de_contrato)
                ])

                if not contrato:
                    msj = "No se encontró el contrato"
                    _logger.info(msj)
                    if solicitud:
                        return {"error": msj}
                    else:
                        continue

                ### Construir diccionario con datos a actualizar ###
                actualizar = {}

                if afi['afiliado_nombre'] != contrato.partner_name:
                    actualizar.update({'partner_name': afi['afiliado_nombre']})

                if afi['afiliado_apellidoPaterno'] != contrato.partner_fname:
                    actualizar.update({'partner_fname': afi['afiliado_apellidoPaterno']})

                if afi['afiliado_apellidoMaterno'] != contrato.partner_mname:
                    actualizar.update({'partner_mname': afi['afiliado_apellidoMaterno']})

                if fields.Date.to_date(afi['afiliado_fechaNacimiento']) != contrato.birthdate:
                    actualizar.update({'birthdate': afi['afiliado_fechaNacimiento']})

                if afi['afiliado_telefono'] != contrato.phone_toll:
                    actualizar.update({'phone_toll': afi['afiliado_telefono']})

                if afi['afiliado_email'] != contrato.client_email:
                    actualizar.update({'client_email': afi['afiliado_email']})

                ### Domicilio de casa ###
                if afi['domCasa_Calle'] != contrato.street_name:
                    actualizar.update({'street_name': afi['domCasa_Calle']})

                casa_num = ""
                if len(afi['domCasa_numInt']) > 0:
                    casa_num = "{} - {}".format(afi['domCasa_numExt'], afi['domCasa_numInt'])
                else:
                    casa_num = afi['domCasa_numExt']

                if casa_num != contrato.street_number:
                    actualizar.update({'street_number': casa_num})

                if afi['domCasa_EntreCalles'] != contrato.between_streets:
                    actualizar.update({'between_streets': afi['domCasa_EntreCalles']})

                # Buscar municipio casa. Si no existe crear
                if afi['domCasa_Municipio']:
                    nombre = afi['domCasa_Municipio']
                    municipio = municipality_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre)
                    ], limit = 1)

                    # Si no existe el municipio, crearlo. Tomar los otros datos del primer registro
                    if not municipio:
                        mun = municipality_obj.search([('company_id', '=', company_id)], limit = 1)

                        if not mun:
                            msj = "No existen municipios"
                            _logger.error(msj)
                            if solicitud:
                                return {"error": msj}
                            else:
                                return

                        id_municipio = municipality_obj.create({
                            'name': nombre,
                            'country_id': mun.country_id.id,
                            'state_id': mun.state_id.id,
                            'company_id': company_id
                        }).id

                        _logger.info("Se crea municipio de casa {}".format(nombre))
                    else:
                        id_municipio = municipio.id

                if id_municipio == 0:
                    msj = "No se pudo obtener el municipio de casa"
                    _logger.error(msj)
                    if solicitud:
                        return {"error": msj}
                    else:
                        continue

                if id_municipio != contrato.municipality_id.id:
                    actualizar.update({'municipality_id': id_municipio})

                # Buscar colonia casa. Si no existe crear #
                if afi['domCasa_Colonia']:
                    nombre = afi['domCasa_Colonia']
                    colonia = colonia_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre),
                        ('municipality_id', '=', id_municipio)
                    ], limit = 1)

                    # Si no existe la colonia, crearla
                    if not afi['domCasa_codigoPostal']:
                        msj = "No se definió el codigo postal de la colonia de casa"
                        _logger.error(msj)
                        if solicitud:
                            return {"error": msj}
                        else:
                            continue

                    if not colonia:
                        id_colonia = colonia_obj.create({
                            'name': nombre,
                            'municipality_id': id_municipio,
                            'company_id': company_id,
                            'zip_code': afi['domCasa_codigoPostal']
                        }).id

                        _logger.info("Se crea colonia de casa {}".format(nombre))
                    else:
                        id_colonia = colonia.id

                if id_colonia == 0:
                    msj = "No se pudo obtener la colonia de casa"
                    _logger.error(msj)
                    if solicitud:
                        return {"error": msj}
                    else:
                        continue

                if id_colonia != contrato.neighborhood_id.id:
                    actualizar.update({'neighborhood_id': id_colonia, 'zip_code': afi['domCasa_codigoPostal']})

                ### Domicilio de cobro ###
                if afi['domCobro_Calle'] != contrato.street_name_toll:
                    actualizar.update({'street_name_toll': afi['domCobro_Calle']})

                cobro_num = ""
                if len(afi['domCobro_numInt']) > 0:
                    cobro_num = "{} - {}".format(afi['domCobro_numExt'], afi['domCobro_numInt'])
                else:
                    cobro_num = afi['domCobro_numExt']

                if cobro_num != contrato.street_number_toll:
                    actualizar.update({'street_number_toll': cobro_num})

                if afi['domCobro_entreClles'] != contrato.between_streets_toll:
                    actualizar.update({'between_streets_toll': afi['domCobro_entreClles']})

                # Buscar municipio cobro. Si no existe crear
                if afi['domCobro_Municipio']:
                    nombre = afi['domCobro_Municipio']
                    municipio = municipality_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre)
                    ], limit = 1)

                    # Si no existe el municipio, crearlo. Tomar los otros datos del primer registro
                    if not municipio:
                        mun = municipality_obj.search([('company_id', '=', company_id)], limit = 1)

                        if not mun:
                            msj = "No existen municipios"
                            _logger.error(msj)
                            if solicitud:
                                return {"error": msj}
                            else:
                                return

                        id_municipio_cobro = municipality_obj.create({
                            'name': nombre,
                            'country_id': mun.country_id.id,
                            'state_id': mun.state_id.id,
                            'company_id': company_id
                        }).id

                        _logger.info("Se crea municipio de cobro {}".format(nombre))
                    else:
                        id_municipio_cobro = municipio.id
                
                if id_municipio_cobro == 0:
                    msj = "No se pudo obtener el municipio de cobro"
                    _logger.error(msj)
                    if solicitud:
                        return {"error": msj}
                    else:
                        continue

                if id_municipio_cobro != contrato.toll_municipallity_id.id:
                    actualizar.update({'toll_municipallity_id': id_municipio_cobro})
                
                ### Buscar colonia cobro. Si no existe crear ###
                if afi['domCobro_Colonia']:
                    nombre = afi['domCobro_Colonia']
                    colonia = colonia_obj.search([
                        ('company_id', '=', company_id),
                        ('name', '=', nombre),
                        ('municipality_id', '=', id_municipio_cobro)
                    ], limit = 1)

                    # Si no existe la colonia, crearla
                    if not afi['domCobro_codigoPostal']:
                        msj = "No se definió el codigo postal de la colonia de cobro"
                        _logger.error(msj)
                        if solicitud:
                            return {"error": msj}
                        else:
                            continue

                    if not colonia:
                        id_colonia_cobro = colonia_obj.create({
                            'name': nombre,
                            'municipality_id': id_municipio,
                            'company_id': company_id,
                            'zip_code': afi['domCobro_codigoPostal']
                        }).id

                        _logger.info("Se crea colonia de cobro {}".format(nombre))
                    else:
                        id_colonia_cobro = colonia.id

                if id_colonia_cobro == 0:
                    msj = "No se pudo obtener la colonia de cobro"
                    _logger.error(msj)
                    if solicitud:
                        return {"error": msj}
                    else:
                        continue

                if id_colonia_cobro != contrato.toll_colony_id.id:
                    actualizar.update({'toll_colony_id': id_colonia_cobro, 'zip_code_toll': afi['domCobro_codigoPostal']})

                ### Actualizar datos en odoo y ecobro###
                if not actualizar:
                    msj = "No se actualizó porque no hay diferencias"
                    _logger.info(msj)
                    if solicitud:
                        return {"correcto": msj}
                    else:
                        self.MarcarAfiliacionComoActualizadaEnEcobro(url_actualizar_afiliaciones, afi['contrato_id'], 2, "No hay diferencias")
                        continue

                _logger.info("{}".format(actualizar))
                contrato.write(actualizar)
                _logger.info("Actualizada en odoo!")

                if solicitud:
                    return {"correcto": contrato.name}
                else:
                    self.MarcarAfiliacionComoActualizadaEnEcobro(url_actualizar_afiliaciones, afi['contrato_id'], 2, "Actualizado")

            except Exception as ex:
                msj = "Error al actualizar: {}".format(ex)
                _logger.error(msj)

                if solicitud:
                    return {"error": msj[0:248]}
                else:
                    self.MarcarAfiliacionComoActualizadaEnEcobro(url_actualizar_afiliaciones, afi['contrato_id'], 0, ex)

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def MarcarAfiliacionComoActualizadaEnEcobro(self, url_actualizar_afiliaciones, id_registro, estatus, mensaje):
        # estatus 2: actualizado

        data_response = {
            "contratos": [
                {
                    "contrato_id": id_registro,
                    "registrada": estatus,
                    "resultado": mensaje
                }
            ]
        }

        llamada = requests.post(url_actualizar_afiliaciones, json=data_response)
        
        respuesta = json.loads(llamada.text)

        if len(respuesta['success']) > 0:
            _logger.info("Actualizada en eCobro!!")
        else:
            _logger.error("No actualizada en eCobro") 

#################################################################################################################################################
######################################                SINCRONIZADOR DE CORTES             #######################################################
#################################################################################################################################################

    ### Cuando no se envia una solicitud ejecuta los web services de consulta de ecobro
    def SincronizarCortes(self, company_id, solicitud):
        _logger.info("Comienza sincronización de cortes")

        array_cortes = []
        url_obtener_cortes = ""
        url_actualizar_corte = ""

        ### Validar cuentas para creación de póliza ###
        info_de_cuentas = {}
        info_de_cuentas = self.ValidarCuentas(company_id, info_de_cuentas)

        if not info_de_cuentas:
            return {'error': "No se encontraron las cuentas para la poliza"}

        if solicitud:
            if 'contrato' not in solicitud.keys() or 'periodo' not in solicitud.keys() or 'fecha_cierre_periodo' not in solicitud.keys():
                return {'error': "Falta algunos de las llaves (contrato, periodo, fecha_cierre_periodo)"}
            
            if not solicitud['contrato'] or not solicitud['periodo'] or not solicitud['fecha_cierre_periodo']:
                return {'error': "Algunos de los valores esta vacio o es cero (contrato, periodo, fecha_cierre_periodo)"}
            
            array_cortes.append({
                "contrato": solicitud['contrato'],
                "periodo": solicitud['periodo'],
                "fecha_cierre_periodo": solicitud['fecha_cierre_periodo']
            })
        else:
            ### Por web service ###
            url_obtener_cortes = self.get_url(company_id, 3)
            if not url_obtener_cortes:
                _logger.error("No se ha definido la dirección del web service: obtener cortes")
                return

            url_actualizar_corte =  self.get_url(company_id, 4)
            if not url_actualizar_corte:
                _logger.error("No se ha definido la dirección del web service: actualizar cortes")
                return
        
            try:
                _logger.info("Comienza consulta de cortes")
                respuesta = requests.post(url_obtener_cortes)
                json_cortes = json.loads(respuesta.text)
                array_cortes = json_cortes.get('result')
            except Exception as ex:
                _logger.error("Error al consultar los cortes de afiliaciones electrónicas {}".format(ex))
                return
            
            # TEST
            # array_cortes = [
            #     { 
            #         "id": "245",
            #         "promotor_id": "260",
            #         "codigo_promotor": "P0251",
            #         "contrato": "PCD000004",
            #         "periodo": "10",
            #         "fecha_cierre_periodo": "2022-09-28 07:01:47"
            #     },
            #     { 
            #         "id": "246",
            #         "promotor_id": "260",
            #         "codigo_promotor": "P0251",
            #         "contrato": "3NJ003036",
            #         "periodo": "10",
            #         "fecha_cierre_periodo": "2022-09-28 07:01:47"
            #     }
            # ]

        cantidad_cortes = len(array_cortes)
        _logger.info("Cortes obtenidos: {}".format(cantidad_cortes))

        # Calcular fecha de contrato por cierre de mes                
        params = self.env['ir.config_parameter'].sudo()
        actually_day = params.get_param('pabs_custom.actually_day')
        last_day = params.get_param('pabs_custom.last_day')

        corte_obj = self.env['pabs.econtract.move']
        contrato_obj = self.env['pabs.contract']
        
        ### Actualizar registros de corte ###
        for index, cor in enumerate(array_cortes):
            try:
                _logger.info("{} de {}. {}".format(index + 1, cantidad_cortes, cor['contrato']))

                ### Buscar registro de corte
                corte = corte_obj.search([
                    ('company_id', '=', company_id),
                    '|', ('id_contrato.lot_id.name', '=', cor['contrato']), #PCD...
                    ('id_contrato.name', '=', cor['contrato']) #XDJ...
                ])

                if not corte:
                    msj = "No se encontró el registro de pre-corte del contrato {}".format(cor['contrato'])

                    if solicitud:
                        return {'error': msj}
                    else:
                        _logger.error(msj)
                        continue

                if len(corte) > 1:
                    msj = "Se encontró más de un registro de pre-corte"

                    if solicitud:
                        return {'error': msj}
                    else:
                        _logger.error(msj)
                        raise ValidationError(msj)

                if corte.estatus == 'cerrado':
                    msj = "El registro de corte ya fue previamente actualizado"

                    if solicitud:
                        return {"error": msj}
                    else:
                        _logger.warning(msj)
                        self.ActualizarCorteEnEcobro(url_actualizar_corte, cor['id'])
                        continue

                if corte.estatus == 'confirmado':
                    msj = "Ya fue recibida en contratos"

                    if solicitud:
                        return {"error": msj}
                    else:
                        _logger.warning(msj)
                        self.ActualizarCorteEnEcobro(url_actualizar_corte, cor['id'])
                        continue
                
                contrato = contrato_obj.browse(corte.id_contrato.id)

                ### Obtener tiempo local ###
                local = pytz.timezone("Mexico/General")
                local_dt = local.localize(fields.Datetime.to_datetime(cor['fecha_cierre_periodo']), is_dst=None)
                fecha_hora_cierre_utc = local_dt.astimezone(pytz.utc)

                ### Actualizar fecha de contrato (Si se fijó una fecha para los contratos tomar esa fecha) ###
                actualizar = {}

                fecha_creacion = fields.Date.to_date(cor['fecha_cierre_periodo'])

                if actually_day and last_day:
                    fecha_creacion = last_day

                actualizar.update({'invoice_date': fecha_creacion, 'date_of_last_status': datetime.today()})

                ### Si es precontrato actualizar nombre a "Nuevo contrato" (para que genere el número de contrato siguiente en el metodo create_contract) ###
                if contrato.state in ('actived', 'precontract'):
                    actualizar.update({'name': 'Nuevo Contrato', 'state': 'contract'})

                contrato.write(actualizar)

                ### Complementar creación del contrato usando el método pabs_contract.create_contract() ###
                _logger.info("Comienza metodo create_contract()")
                contrato_obj.create_contract(vals={'lot_id' : contrato.lot_id.id})
                _logger.info("Se creó el contrato {}: ".format(contrato.name))

                ### Generar póliza de inversiones y excedentes ###
                id_poliza = self.CrearPoliza(company_id, contrato.invoice_date, contrato.name, contrato.stationery, contrato.initial_investment - contrato.stationery, contrato.sale_employee_id.warehouse_id.analytic_account_id.id, info_de_cuentas)
                
                ### Actualizar registro de cierre en odoo ###
                local = pytz.timezone("Mexico/General")

                local_dt = local.localize(fields.Datetime.to_datetime(cor['fecha_cierre_periodo']), is_dst=None)

                fecha_hora_cierre_utc = local_dt.astimezone(pytz.utc)

                corte.write({
                    'fecha_hora_cierre': fecha_hora_cierre_utc.strftime("%Y-%m-%d %H:%M:%S"),
                    'estatus': 'cerrado',
                    'periodo': cor['periodo'],
                    'id_poliza_caja_transito': id_poliza
                })

                _logger.info("Actualizado en odoo")

                ### Actualizar en eCobro ###
                if solicitud:
                    return {"correcto": contrato.name}
                else:
                    self.ActualizarCorteEnEcobro(url_actualizar_corte, cor['id'])

            except Exception as ex:
                msj = "Error en el proceso de corte: {}".format(ex)
                _logger.error(msj)

                if solicitud:
                    return "error: Error en el proceso de corte: {}".format(msj)
                else:
                    _logger.error(msj)

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

    def CrearRegistroPrecierre(self, company_id, id_asistente, id_contrato):
        _logger.info("Comienza registro de precierre")

        obj_cierre = self.env['pabs.econtract.move']

        #Buscar que no exista registro
        existe_cierre = obj_cierre.search([
            ('company_id', '=', company_id),
            ('id_asistente', '=', id_asistente),
            ('id_contrato', '=', id_contrato)
        ])

        if existe_cierre:
            _logger.warning("Ya existe registro de precierre id_contrato {}".format(id_contrato))
            return

        datos = {
            'company_id': company_id,
            'id_asistente': id_asistente,
            'id_contrato': id_contrato,
            'estatus': 'sin_cierre'
        }

        nuevo = obj_cierre.create(datos)

        _logger.info("Se crea registro de precierre")

        return nuevo

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

        ###################################
        ### Sincronizar cada contrato ### Si ocurre error al actualizar un contrato pasar al siguiente
        for index, con in enumerate(array_contratos):
            try:
                indice = index + 1
                
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
                    'debt_collector': cobrador[0]['id_cobrador'],
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

#################################################################################################################################################
######################################       SINCRONIZACION DE DIRECCIONES ACTUALIZADAS        ##################################################
#################################################################################################################################################

    def ActualizarDirecciones(self, company_id):
        _logger.info("Comienza sincronización de direcciones actualizadas")

        contract_obj = self.env['pabs.contract']

        ### Validar parámetros ###
        if not company_id:
            _logger.error("No se ha definido la compañia")
            return

        ### Validar web service de consulta y respuesta ###
        url_obtener_contratos = self.get_url(company_id, 7)
        if not url_obtener_contratos:
            _logger.error("No se ha definido la dirección del web service: obtener direcciones actualizadas")
            return

        url_actualizar_contratos = self.get_url(company_id, 8)
        if not url_actualizar_contratos:
            _logger.error("No se ha definido la dirección del web service: marcar dirección como actualizada")
            return

        ### Llamar web service de consulta ###
        try:
            _logger.info("Comienza consulta de direcciones")
            data = {"sistema": 1}
            respuesta = requests.post(url_obtener_contratos, json=data)
            json_contratos = json.loads(respuesta.text)
            array_contratos = json_contratos.get('resultado')
        except Exception as ex:
            _logger.error("Error al consultar cobradores {}".format(ex))
            return

        cantidad_contratos = len(array_contratos)
        _logger.info("Contratos obtenidos: {}".format(cantidad_contratos))

        # TEST
        # for i in range(1, cantidad_contratos): # Tomar solo X elementos de la lista
        #     array_contratos.pop(1)
        # cantidad_contratos = len(array_contratos)
        # _logger.info("PRUEBA -> Se recorta a {} contratos".format(cantidad_contratos))

        ###################################
        ### Sincronizar cada contrato ### Si ocurre error al actualizar un contrato pasar al siguiente
        for index, con in enumerate(array_contratos):
            try:
                indice = index + 1
                
                _logger.info("{} de {}. {}".format(indice, cantidad_contratos, con['Contrato']))

                ### Buscar contrato ###
                contrato = contract_obj.search([
                    ('company_id', '=', company_id),
                    ('name', '=', con['Contrato'])
                ])

                if not contrato:
                    raise ValidationError("No se encontró el contrato")

                if len(contrato) > 1:
                    raise ValidationError("Se encontró más de un contrato")

                ### Crear diccionario de actualización
                datos_por_actualizar = {}

                if con['Calle'] and con['Calle'] != contrato.street_name_toll:
                    datos_por_actualizar.update({'street_name_toll': con['Calle']})

                if con['Exterior']:
                    if con['Interior']:
                        if "{}-{}".format(con['Exterior'], con['Interior']) != contrato.street_number_toll:
                            datos_por_actualizar.update({'street_number_toll': "{}-{}".format(con['Exterior'], con['Interior'])})
                    elif con['Exterior'] != contrato.street_number_toll:
                        datos_por_actualizar.update({'street_number_toll': con['Exterior']})

                if con['EntreCalles'] and con['EntreCalles'] != contrato.between_streets_toll:
                    datos_por_actualizar.update({'between_streets_toll': con['EntreCalles']})

                if con['LocCol_LocalidadID'] and con['LocCol_LocalidadID'] != contrato.toll_municipallity_id.id:
                    datos_por_actualizar.update({'toll_municipallity_id': con['LocCol_LocalidadID']})

                if con['LocCol_ColoniaID'] and con['LocCol_ColoniaID'] != contrato.toll_colony_id.id:
                    datos_por_actualizar.update({'toll_colony_id': con['LocCol_ColoniaID']})

                if con['Celular'] and con['Celular'] != "Sin teléfono" and con['Celular'] != contrato.phone_toll:
                    datos_por_actualizar.update({'phone_toll': con['Celular']})
                
                if con['Correo'] and con['Correo'] != contrato.client_email:
                    datos_por_actualizar.update({'client_email': con['Correo']})

                ### Actualizar contrato ###
                if datos_por_actualizar:
                    contrato.write(datos_por_actualizar)

                    _logger.info("Actualizado en Odoo")
                else:
                    _logger.info("No hay datos por actualizar")

                estatus = 1
     
                self.ActualizarDireccionEnEcobro(url_actualizar_contratos, con['IDRegistro'], estatus)

            except Exception as ex:
                estatus = 2
                _logger.error("Error al actualizar dirección: {}".format(ex))
                self.ActualizarDireccionEnEcobro(url_actualizar_contratos, con['IDRegistro'], estatus)  

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    
    # estatus 0: no actualizado
    # estatus 1: actualizado
    # estatus 2: error al actualizar
    # estatus 3: error al utilizar web service de actualización    
    def ActualizarDireccionEnEcobro(self, url_actualizar_contratos, id_registro, estatus):
        data_response = {
            "result": [
                {
                    "IDRegistro": id_registro, 
			        "Estatus": estatus
                }
            ]
        }

        llamada = requests.post(url_actualizar_contratos, json=data_response)
        
        respuesta = json.loads(llamada.text)

        if len(respuesta['success']) > 0:
            _logger.info("Actualizado en eCobro")
        else:
            raise ValidationError("No actualizada en eCobro")