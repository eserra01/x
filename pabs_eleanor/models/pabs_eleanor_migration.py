# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import json

import logging
_logger = logging.getLogger(__name__)

# Id de la sucursal en Eleanor
BASES_ELEANOR = {
    'GUADALAJARA': 2,
    'FUNERARIA_GDL': 14,

    ### PRODUCCION ###
    'TOLUCA': 13,
    'PUEBLA': 5,
    'SALTILLO NUEVO E': 6,
    'MERIDA': 3,
    'CANCUN': 1,
    'CUERNAVACA': 4,
    'TAMPICO NUEVO E': 10,
    'ACAPULCO NUEVO E': 8,
    'MONCLOVA NUEVO E': 7,
    'NUEVO LAREDO NUEVO E': 9,
    'TUXTLA GUTIERREZ': 11,
    'VILLAHERMOSA': 12

    ### TEST
    ,'SALTILLO': 6,
    'MONCLOVA': 7,
    'NUEVO LAREDO': 9
}

class PabsEleanorMigrationLog(models.Model):
    _name = 'pabs.eleanor.migration.log'
    _description = 'Log de migración de base Eleanor'
    _rec_name = "mensaje"

    tabla = fields.Char(string="Tabla")
    registro = fields.Char(string="Registro")
    mensaje = fields.Char(string="Mensaje")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,)

    # log_obj = self.env['pabs.eleanor.migration.log']

    # log_obj.create([{
    #     'tabla': 'Areas',
    #     'registro': 'registro 1',
    #     'mensaje': 'Exito',
    # }])

class PabsEleanorMigration(models.TransientModel):
    _name = 'pabs.eleanor.migration'
    _description = 'Migración de base Eleanor'

    def ConsultaECO_ODOO(self, query):
        ### Consulta a ECO ODOO de plantillas a crear
        plaza = "ELEANOR"

        url = "http://nomina.dyndns.biz:8098/index.php"

        querystring = {"pwd":"4dm1n","plaza": plaza}

        # payload = "consulta=EXEC%20%5Bdig%5D.%5BComentariosPorCrear%5D%20%40default%20%3D%200"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.request("POST", url, data=query, headers=headers, params=querystring)
        
        return json.loads(response.text)

################################################################################
    def CrearAreas(self):
        _logger.info("Comienza creación de areas")

        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        area_obj = self.env['pabs.eleanor.area']

        cant = area_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Areas', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        area_obj.create([
            {'name': 'ASISTENCIA SOCIAL', 'company_id': id_compania},
            {'name': 'ADMINISTRACIÓN Y RECUPERACIÓN', 'company_id': id_compania},
            {'name': 'FUNERARIA', 'company_id': id_compania},
            {'name': 'DIREMOVIL', 'company_id': id_compania}
        ])

        cant = area_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        _logger.info("Areas creadas: {}".format(cant))

################################################################################
    def CrearDepartamentosOficinas(self):
        _logger.info("Comienza creación de departamentos y oficinas")
        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        dep_obj = self.env['hr.department']
        ofi_obj = self.env['stock.warehouse']
        
        ### Consultar departamentos y oficinas de Odoo
        departamentos_odoo = dep_obj.search([
            ('company_id', '=', id_compania)
        ])

        oficinas_odoo = ofi_obj.search([
            ('company_id', '=', id_compania),
            ('active', 'in', (True, False))
        ])

        ### Consultar oficinas de Eleanor
        if not self.env.company.name in BASES_ELEANOR:
            _logger.info("No se puede determinar el id de la base de Eleanor")
            log_obj.create([{'tabla': 'Actualizar areas', 'registro': self.env.company.name, 'mensaje': "No se puede determinar el id de la base de Eleanor"}])
            return

        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BOficinas%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        oficinas_eleanor = []
        for res in respuesta:
            oficinas_eleanor.append({
                'tipo': res['tipo'],
                'nombre': res['nombre'],
                'area': res['area'],
                'cuenta_analitica': res['cuenta_analitica']
            })

        creados = 0
        for ofi_ele in oficinas_eleanor:
            
            ### Encontrar departamento de Odoo
            if ofi_ele['tipo'] == 'departamento':
                dep = next((x for x in departamentos_odoo if x.name == ofi_ele['nombre']), 0)

                if not dep:
                    dep_obj.create({
                        'name': ofi_ele['nombre'],
                        'company_id': id_compania
                    })

                    creados = creados + 1
            else:
                ofi = next((x for x in oficinas_odoo if x.name == ofi_ele['nombre']), 0)

                if not ofi:
                    ofi_obj.create({
                        'name': ofi_ele['nombre'],
                        'active': False,
                        'code': ofi_ele['nombre'][0:6],
                        'company_id': id_compania
                    })

                    creados = creados + 1

        _logger.info("Departamentos y oficinas creados: {}".format(creados))

################################################################################
    def CrearCuentasAnaliticas(self):
        _logger.info("Comienza creación de cuentas analíticas")
        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        cue_obj = self.env['account.analytic.account']
        
        ### Consultar cuentas analíticas de Odoo
        cuentas_odoo = cue_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar cuentas de Eleanor
        if not self.env.company.name in BASES_ELEANOR:
            _logger.info("No se puede determinar el id de la base de Eleanor")
            log_obj.create([{'tabla': 'Actualizar areas', 'registro': self.env.company.name, 'mensaje': "No se puede determinar el id de la base de Eleanor"}])
            return

        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BOficinas%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        cuentas_eleanor = []
        for res in respuesta:
            if {'cuenta': res['cuenta_analitica']} not in cuentas_eleanor:
                cuentas_eleanor.append({'cuenta': res['cuenta_analitica']})

        creados = 0
        for cue_ele in cuentas_eleanor:
            
            ### Encontrar cuenta analítica de Odoo
            cue = next((x for x in cuentas_odoo if x.name == cue_ele['cuenta']), 0)

            if not cue:
                cue_obj.create({
                    'name': cue_ele['cuenta'],
                    'company_id': id_compania
                })

                creados = creados + 1

        _logger.info("Cuentas analíticas creadas: {}".format(creados))

################################################################################
    def ActualizarAreas(self):
        _logger.info("Comienza asignacion de areas y cuentas a oficinas y departamentos")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']

        ofi_obj = self.env['stock.warehouse']
        dep_obj = self.env['hr.department']
        cue_obj = self.env['account.analytic.account']
        area_obj = self.env['pabs.eleanor.area']

        ### Consultar areas, oficinas, departamentos y cuentas analíticas de Odoo
        areas_odoo = area_obj.search([
            ('company_id', '=', id_compania)
        ])

        if not areas_odoo:
            _logger.info("No hay areas en Odoo")
            log_obj.create([{'tabla': 'Actualizar areas', 'registro': '', 'mensaje': "No hay areas en ODOO"}])

            return

        oficinas_odoo = ofi_obj.search([
            ('company_id', '=', id_compania),
            ('active', 'in', (True, False))
        ])
        
        departamentos_odoo = dep_obj.search([
            ('company_id', '=', id_compania)
        ])

        cuentas_odoo = cue_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar oficinas de Eleanor
        if not self.env.company.name in BASES_ELEANOR:
            _logger.info("No se puede determinar el id de la base de Eleanor")
            log_obj.create([{'tabla': 'Actualizar areas', 'registro': self.env.company.name, 'mensaje': "No se puede determinar el id de la base de Eleanor"}])
            return

        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BOficinas%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        oficinas_eleanor = []
        for res in respuesta:
            oficinas_eleanor.append({
                'tipo': res['tipo'],
                'nombre': res['nombre'],
                'area': res['area'],
                'cuenta_analitica': res['cuenta_analitica']
            })

        actualizados = 0
        errores = 0

        for ofi in oficinas_eleanor:
            reg = None
            if ofi['tipo'] == 'departamento':
                ### Buscar departamento de Odoo
                reg = next((x for x in departamentos_odoo if x.name == ofi['nombre']), 0)

                if not reg:
                    log_obj.create([{
                        'tabla': 'Actualizar areas', 
                        'registro': ofi['nombre'], 
                        'mensaje': "No se encontró departamento"
                    }])

                    errores = errores + 1
                    continue
            else:
                ### Buscar oficina de Odoo
                reg = next((x for x in oficinas_odoo if x.name == ofi['nombre']), 0)

                if not reg:
                    log_obj.create([{
                        'tabla': 'Actualizar areas', 
                        'registro': ofi['nombre'], 
                        'mensaje': "No se encontró oficina"
                    }])
                
                    errores = errores + 1
                    continue
            
            ### Encontrar area de Odoo
            area_odoo = next((x for x in areas_odoo if x.name == ofi['area']), 0)

            if not area_odoo:
                log_obj.create({
                    'tabla': 'Actualizar areas', 
                    'registro': ofi['nombre'], 
                    'mensaje': 'No se encontró área {}'.format(ofi['area'])
                })

                errores = errores + 1
                continue

            ### Encontrar cuenta analítica de Odoo
            cuenta_odoo = next((x for x in cuentas_odoo if x.name == ofi['cuenta_analitica']), 0)

            if not cuenta_odoo:
                log_obj.create({
                    'tabla': 'Actualizar areas', 
                    'registro': ofi['nombre'], 
                    'mensaje': 'No se encontró cuenta analitica {}'.format(ofi['cuenta_analitica'])
                })

                errores = errores + 1
                continue
            
            ### Actualizar registro
            vals = {}

            if reg.pabs_eleanor_area_id.id != area_odoo.id:
                vals.update({'pabs_eleanor_area_id': area_odoo.id})

            if ofi['tipo'] == 'departamento':
                if reg.account_analytic_id.id != cuenta_odoo.id:
                    vals.update({'account_analytic_id': cuenta_odoo.id})
            else:
                if reg.analytic_account_id.id != cuenta_odoo.id:
                    vals.update({'analytic_account_id': cuenta_odoo.id})
            
            if vals:
                reg.write(vals)
                actualizados = actualizados + 1

        _logger.info("Asignar area/cuenta en ofi/dep >>> Actualizadas: {}, Errores: {}".format(actualizados, errores))

################################################################################
    def CrearPuestos(self):
        _logger.info("Comienza creación de puestos")
        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        pue_obj = self.env['hr.job']
        
        ### Consultar puestos de Odoo
        puestos_odoo = pue_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar puestos de Eleanor
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BCategorias_puestos%5D%20"
        respuesta = self.ConsultaECO_ODOO(query)

        puestos_eleanor = []
        for res in respuesta:
            if {'puesto': res['puesto']} not in puestos_eleanor:
                puestos_eleanor.append({'puesto': res['puesto']})

        creados = 0
        for pue in puestos_eleanor:
            exi = next((x for x in puestos_odoo if x.name == pue['puesto']), 0)

            if not exi:
                pue_obj.create({
                    'name': pue['puesto'],
                    'company_id': id_compania
                })

                creados = creados + 1

        _logger.info("Puestos creados: {}".format(creados))

################################################################################
    def CrearCategoriasPuestos(self):
        _logger.info("Comienza creación de categorias de puestos")
        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        cat_obj = self.env['pabs.eleanor.job.category']

        cant = cat_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Categorias de puestos', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ### Consultar puestos
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BCategorias_puestos%5D%20"
        respuesta = self.ConsultaECO_ODOO(query)

        ### Dejar un solo registro de categoria
        categorias = []
        categorias_aux = []
        for res in respuesta:
            if res['categoria'] not in categorias_aux:
                categorias_aux.append(res['categoria'])

                categorias.append({
                    'name': res['categoria'],
                    'identifier': res['identificador'],
                    'dependence': res['dependencia']
                })

        cat_obj.create(categorias)

        _logger.info("Categorias de puestos creados: {}".format(len(categorias)))

################################################################################
    def ActualizarCategoriasPuestos(self):
        _logger.info("Comienza actualización de puestos")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']
        puesto_obj = self.env['hr.job']
        categoria_obj = self.env['pabs.eleanor.job.category']

         ### Consultar categorias de puestos de Odoo
        categorias_odoo = categoria_obj.search([
            ('company_id', '=', id_compania)
        ])

        if not categorias_odoo:
            _logger.info("No hay categorias en Odoo")
            log_obj.create([{'tabla': 'Actualizar categorias de puestos', 'registro': '', 'mensaje': "No hay categorias en ODOO"}])
            
            return

        ### Consultar puestos de Odoo
        puestos_odoo = puesto_obj.search([
            ('company_id', '=', id_compania)
        ], order="name")

        ### Consultar categorias de Eleanor
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BCategorias_puestos%5D"
        respuesta = self.ConsultaECO_ODOO(query)

        categorias_eleanor = []
        for res in respuesta:
            if res['categoria']:
                categorias_eleanor.append({
                    'puesto': res['puesto'],
                    'categoria': res['categoria'],
                    'identificador': res['identificador'],
                    'dependencia': res['dependencia']
                })

        actualizados = 0
        errores = 0

        for cat in categorias_eleanor:
            ### Encontrar puesto de Odoo
            pue = next((x for x in puestos_odoo if x.name == cat['puesto']), 0)

            if not pue:
                log_obj.create([{'tabla': 'Actualizar categorias de puestos', 'registro': cat['puesto'], 'mensaje': "No se encontró puesto"}])
                errores = errores + 1
                continue

            ### Encontrar categoria de Odoo
            cat_odoo = next((x for x in categorias_odoo if x.name == cat['categoria']), 0)

            if not cat_odoo:
                log_obj.create([{'tabla': 'Actualizar categorias de puestos', 'registro': cat['categoria'], 'mensaje': "No se encontró la categoría"}])
                errores = errores + 1
                continue
            
            if pue.job_category_id.id != cat_odoo.id:
                pue.write({'job_category_id': cat_odoo.id})

                actualizados = actualizados + 1

        _logger.info("Actualizados: {}, Errores: {}".format(actualizados, errores))

################################################################################
    def CrearEnfermedades(self):
        _logger.info("Comienza creación de enfermedades")

        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        enf_obj = self.env['pabs.eleanor.disease']

        cant = enf_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Enfermedades', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        enf_obj.create([
            {'name': 'MATERNIDAD', 'company_id': id_compania},
            {'name': 'PATERNIDAD', 'company_id': id_compania},
            {'name': 'ENFERMEDAD GENERAL', 'company_id': id_compania},
            {'name': 'RIESGO DE TRABAJO', 'company_id': id_compania}
        ])

        cant = enf_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        _logger.info("Enfermedades creadas: {}".format(cant))

################################################################################
    def MigrarEmpleados(self, coincidencia_exacta):
        _logger.info("Comienza creación y actualización de empleados")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']
        emp_obj = self.env['hr.employee']

        pue_obj = self.env['hr.job']
        dep_obj = self.env['hr.department']
        ofi_obj = self.env['stock.warehouse']
        est_obj = self.env['hr.employee.status']
        
        mx_obj = self.env['res.country.state']
        mun_obj = self.env['res.locality']
        col_obj = self.env['colonias']

        ### Consultar registros de Odoo        
        oficinas = ofi_obj.search([
            ('company_id', '=', id_compania),
            ('active', 'in', (True, False))
        ])

        departamentos = dep_obj.search([
            ('company_id', '=', id_compania)
        ])

        depto_ventas = next((x for x in departamentos if x.name == "VENTAS"), 0)

        if not depto_ventas:
            _logger.info("No se encontró el departamento VENTAS")
            log_obj.create([{'tabla': 'Migrar empleados', 'registro': '', 'mensaje': "No existe el departamento VENTAS"}])
            return

        puestos = pue_obj.search([
            ('company_id', '=', id_compania)
        ])
        
        estatus = est_obj.search([
            ('id', '>', 0)
        ])
        
        empleados_odoo = emp_obj.search([
            ('company_id', '=', id_compania)
        ])

        estados_mx = mx_obj.search([
            ('country_id', '=', 156)
        ])

        municipios = mun_obj.search([
            ('company_id', '=', id_compania)
        ])

        colonias = col_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar empleados de Eleanor
        if not self.env.company.name in BASES_ELEANOR:
            _logger.info("No se puede determinar el id de la base de Eleanor")
            log_obj.create([{'tabla': 'Migrar empleados', 'registro': self.env.company.name, 'mensaje': "No se puede determinar el id de la base de Eleanor"}])
            return
        
        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BEmpleados%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        empleados_eleanor = []
        for res in respuesta:
            empleados_eleanor.append({
                'id_eleanor': int(res['id_eleanor']),
                'codigo': res['codigo'],
                'nombre': res['nombre'],
                'estado_civil': res['estado_civil'],
                'fecha_nacimiento': res['fecha_nacimiento'],
                'domicilio': res['domicilio'],
                'colonia': res['colonia'],
                'municipio': res['municipio'],
                'estado': res['estado'],
                'cp': res['cp'],
                'telefono': res['telefono'],
                'nss': res['nss'],
                'rfc': res['rfc'],
                'curp': res['curp'],
                'estatus': res['estatus'],
                'comentarios': res['comentarios'],
                'fecha_alta': res['fecha_alta'],
                'lugar_nacimiento': res['lugar_nacimiento'],
                'nombre_padre': res['nombre_padre'],
                'nombre_madre': res['nombre_madre'],
                'infonavit': res['infonavit'],
                'patron': res['patron'],
                'salario_interno_total': float(res['salario_interno_total']),
                'salario_diario': float(res['salario_diario']),
                'salario_diario_integrado': float(res['salario_diario_integrado']),
                'amortizacion_infonavit': res['amortizacion_infonavit'],
                'valor_descuento': float(res['valor_descuento']),
                'conflicto': res['conflicto'],
                'parentesco': res['parentesco'],
                'tipo_periodo': res['tipo_periodo'],
                'puesto': res['puesto'],
                'forma_pago': res['forma_pago'],
                'oficina': res['oficina'],
                'area': res['area'],
                'adj_expediente': res['adj_expediente'],
                'adj_alta': res['adj_alta']
            })

        creados = 0
        actualizados = 0
        errores = 0
        cantidad_registros = len(empleados_eleanor)

        for index, emp in enumerate(empleados_eleanor, 1):
            _logger.info("{} de {}. {} {}".format(index, cantidad_registros, emp['codigo'], emp['nombre']))

            ### Buscar empleado por id de eleanor
            emp_act = next(((x for x in empleados_odoo if x.eleanor_id == emp['id_eleanor'])), 0)
            
            if not emp_act:
                ### Buscar empleado por codigo y nombre
                coincidencias_codigo = list((x for x in empleados_odoo if x['barcode'] == emp['codigo']))

                for exi in coincidencias_codigo:
                    
                    ### Quitar espacios extra
                    nombre = " ".join(exi.first_name.split()).upper()
                    apellido = " ".join(exi.last_name.split()).upper()

                    ### Quitar acentos (En la consulta hacia Eleanor se aplicaron los mismos reemplazos)
                    nombre = nombre.replace('Á', 'A')
                    nombre = nombre.replace('É', 'E')
                    nombre = nombre.replace('Í', 'I')
                    nombre = nombre.replace('Ó', 'O')
                    nombre = nombre.replace('Ú', 'U')

                    apellido = apellido.replace('Á', 'A')
                    apellido = apellido.replace('É', 'E')
                    apellido = apellido.replace('Í', 'I')
                    apellido = apellido.replace('Ó', 'O')
                    apellido = apellido.replace('Ú', 'U')
                    
                    nombre_apellidos = "{} {}".format(nombre, apellido)
                    apellidos_nombre = "{} {}".format(apellido, nombre)
                    
                    if coincidencia_exacta:
                        if nombre_apellidos == emp['nombre'] or apellidos_nombre == emp['nombre'] or exi.name == emp['nombre']:
                            emp_act = exi
                            break
                    else:
                        if apellido in emp['nombre'] or nombre in emp['nombre']:
                            emp_act = exi
                            break

                if coincidencias_codigo and not emp_act:
                    log_obj.create([{
                        'tabla': 'Migrar empleados', 
                        'registro': "{} {}".format(emp['codigo'], emp['nombre']),
                        'mensaje': "Ya existe el código pero no coincide el nombre" 
                    }])
                    errores = errores + 1
                    continue
            
            ### Encontrar estado de lugar de nacimento
            id_lugar_nac = None

            lugar_nac = next((x for x in estados_mx if x.name.upper() == emp['lugar_nacimiento']), 0)
            if lugar_nac:
                id_lugar_nac = lugar_nac.id

            ### Encontrar estado de domicilio
            id_estado = None
            
            estado = next((x for x in estados_mx if x.name.upper() == emp['estado']), 0)
            if estado:
                id_estado = estado.id

            ### Encontrar municipio
            id_municipio = None
            id_colonia = None

            mun = next((x for x in municipios if x.name == emp['municipio']), 0)

            if mun:
                id_municipio = mun.id

                ### Encontrar colonia
                col = next((x for x in colonias if x.municipality_id.id == mun.id and x.name == emp['colonia']), 0)

                if col:
                    id_colonia = col.id

            ########## Actualizar empleado ##########
            if emp_act:
                vals = {}

                # Campos existentes (Se actualizan si el valor es diferente)
                if emp['fecha_alta'] != "1910-01-01" and str(emp_act.date_of_admission) != emp['fecha_alta']:
                    vals.update({'date_of_admission': emp['fecha_alta']})

                if emp['fecha_nacimiento'] != "1910-01-01" and str(emp_act.birthday) != emp['fecha_nacimiento']:
                    vals.update({'birthday': emp['fecha_nacimiento']})

                if emp['comentarios'] and emp['comentarios'] not in str(emp_act.comment):
                    if emp_act.comment:
                        vals.update({'comment': "{} | {}".format(emp_act.comment, emp['comentarios'])})
                    else:
                        vals.update({'comment': emp['comentarios']})
                    
                if id_municipio and emp_act.municipality_id.id != id_municipio: vals.update({'municipality_id': id_municipio})
                if id_colonia and emp_act.neighborhood_id.id != id_colonia: vals.update({'neighborhood_id': id_colonia})
                if id_estado and emp_act.state_id.id != id_estado: vals.update({'state_id': id_estado})

                if emp['domicilio'] and emp_act.street != emp['domicilio']: vals.update({'street': emp['domicilio']})
                if emp['cp'] and emp_act.zip != emp['cp']: vals.update({'zip': emp['cp']})
                if emp['telefono'] and emp_act.mobile_phone != emp['telefono']: vals.update({'mobile_phone': emp['telefono']})
                if emp['estado_civil'] and emp_act.marital != emp['estado_civil']: vals.update({'marital': emp['estado_civil']})
                if emp['nss'] and emp_act.nss != emp['nss']: vals.update({'nss': emp['nss']})
                if emp['rfc'] and emp_act.rfc != emp['rfc']: vals.update({'rfc': emp['rfc']})
                if emp['curp'] and emp_act.curp != emp['curp']: vals.update({'curp': emp['curp']})

                # Campos nuevos (Se actualizan si no existe valor)
                if emp_act.eleanor_id != emp['id_eleanor']: vals.update({'eleanor_id': emp['id_eleanor']})

                if emp_act.total_internal_salary != emp['salario_interno_total']: vals.update({'total_internal_salary': emp['salario_interno_total']})
                if emp_act.daily_salary != emp['salario_diario']: vals.update({'daily_salary': emp['salario_diario']})
                if emp_act.integrated_daily_salary != emp['salario_diario_integrado']: vals.update({'integrated_daily_salary': emp['salario_diario_integrado']})
                if emp_act.discount_value != emp['valor_descuento']: vals.update({'discount_value': emp['valor_descuento']})

                if not emp_act.fathers_name and emp['nombre_padre']: vals.update({'fathers_name': emp['nombre_padre']})
                if not emp_act.mothers_name and emp['nombre_madre']: vals.update({'mothers_name': emp['nombre_madre']})
                if not emp_act.birth_place and id_lugar_nac: vals.update({'birth_place': id_lugar_nac})
                if not emp_act.infonavit_credit and emp['infonavit']: vals.update({'infonavit_credit': emp['infonavit']})
                if not emp_act.boss and emp['patron']: vals.update({'boss': emp['patron']})
                if not emp_act.personal_file_name and emp['adj_expediente']: vals.update({'personal_file_name': emp['adj_expediente']})
                if not emp_act.constancy_up_name and emp['adj_alta']: vals.update({'constancy_up_name': emp['adj_alta']})
                if not emp_act.infonavit_credit_amortization and emp['amortizacion_infonavit']: vals.update({'infonavit_credit_amortization': emp['amortizacion_infonavit']})
                if not emp_act.interest_conflict and emp['conflicto']: vals.update({'interest_conflict': emp['conflicto']})
                if not emp_act.period_type and emp['tipo_periodo']: vals.update({'period_type': emp['tipo_periodo']})
                if not emp_act.way_to_pay and emp['forma_pago']: vals.update({'way_to_pay': emp['forma_pago']})

                if vals:
                    emp_act.write(vals)

                    actualizados = actualizados + 1
                    _logger.info("Actualizado")

            ########## Crear empleado ##########
            else:
                ### Encontrar puesto
                pue = next((x for x in puestos if x.name == emp['puesto']), 0)

                if not pue:
                    log_obj.create([{
                        'tabla': 'Migrar empleados', 
                        'registro': "{}".format(emp['codigo']), 
                        'mensaje': "No se encontró el puesto {}".format(emp['puesto'])
                    }])
                    errores = errores + 1
                    continue

                ### Encontrar estatus
                est = next((x for x in estatus if x.name == emp['estatus']), 0)

                if not est:
                    log_obj.create([{
                        'tabla': 'Migrar empleados', 
                        'registro': "{}".format(emp['codigo']), 
                        'mensaje': "No se encontró el estatus {}".format(emp['estatus'])
                    }])
                    errores = errores + 1
                    continue
                
                ### Encontrar departamento
                id_departamento = None
                id_oficina = None

                if emp['area'] == "ASISTENCIA SOCIAL":
                    id_departamento = depto_ventas.id

                    ### Encontrar oficina
                    ofi = next((x for x in oficinas if x.name == emp['oficina']), 0)

                    if ofi:
                        id_oficina = ofi.id
                    else:
                        log_obj.create([{
                            'tabla': 'Migrar empleados', 
                            'registro': "{}".format(emp['codigo']), 
                            'mensaje': "No se encontró la oficina de ventas {}".format(emp['oficina'])
                        }])
                        errores = errores + 1
                        continue
                else:
                    dep = next((x for x in departamentos if x.name == emp['oficina']), 0)

                    if dep:
                        id_departamento = dep.id
                    else:
                        log_obj.create([{
                            'tabla': 'Migrar empleados', 
                            'registro': "{}".format(emp['codigo']), 
                            'mensaje': "No se encontró el departamento {}".format(emp['oficina'])
                        }])
                        errores = errores + 1
                        continue

                # Dividir el nombre en dos palabras
                palabras = emp['nombre'].split()
                palabra_1 = ""
                palabra_2 = ""

                if len(palabras) >= 2:
                    palabra_1 = palabras[0]
                    palabra_2 = " ".join(palabras[1:99])
                else:
                    palabra_1 = emp['nombre']
                    palabra_2 = "X"

                id_creacion = emp_obj.with_context(migration=True).create({
                    'company_id': id_compania,
                    'eleanor_id': emp['id_eleanor'],
                    'barcode': emp['codigo'],
                    'name': emp['nombre'],
                    'first_name': palabra_1,
                    'last_name': palabra_2,
                    'job_id': pue.id,
                    'date_of_admission': emp['fecha_alta'],
                    'employee_status': est.id,
                    'warehouse_id': id_oficina,
                    'department_id': id_departamento,
                    'marital': emp['estado_civil'],
                    'comment': emp['comentarios'],
                    'fathers_name': emp['nombre_padre'],
                    'mothers_name': emp['nombre_madre'],
                    'birthday': emp['fecha_nacimiento'],
                    'birth_place': id_lugar_nac,
                    'street': emp['domicilio'],
                    'municipality_id': id_municipio,
                    'neighborhood_id': id_colonia,
                    'state_id': id_estado,
                    'zip': emp['cp'],
                    'mobile_phone': emp['telefono'],
                    'nss': emp['nss'],
                    'rfc': emp['rfc'],
                    'curp': emp['curp'],
                    'infonavit_credit': emp['infonavit'],
                    'boss': emp['patron'],
                    'total_internal_salary': emp['salario_interno_total'],
                    'daily_salary': emp['salario_diario'],
                    'integrated_daily_salary': emp['salario_diario_integrado'],
                    'personal_file_name': emp['adj_expediente'],
                    'constancy_up_name': emp['adj_alta'],
                    'infonavit_credit_amortization': emp['amortizacion_infonavit'] if emp['amortizacion_infonavit'] else None,
                    'discount_value': emp['valor_descuento'],
                    'interest_conflict': emp['conflicto'],
                    'relationship': emp['parentesco'],
                    'period_type': emp['tipo_periodo'],
                    'way_to_pay': emp['forma_pago']
                })

                if id_creacion:
                    creados = creados + 1
                    _logger.info("Creado")
                else:
                    log_obj.create([{
                        'tabla': 'Migrar empleados', 
                        'registro': "{}".format(emp['codigo']), 
                        'mensaje': "No se creó el empleado, revisar oficina {}".format(emp['oficina'])
                    }])
                    errores = errores + 1
            
        _logger.info("Migrar Empleados >>> Creados: {}, Actualizados: {}, Errores: {}".format(creados, actualizados, errores))

################################################################################
    def CrearIncapacidades(self):
        _logger.info("Comienza creación de incapacidades")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']
        emp_obj = self.env['hr.employee']
        enf_obj = self.env['pabs.eleanor.disease']
        inc_obj = self.env['pabs.eleanor.inability']

        ### Validar que no existan registros
        cant = inc_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Incapacidades', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ## Consultar enfermedades y empleados de Odoo
        enfermedades = enf_obj.search([
            ('company_id', '=', id_compania)
        ])

        if not enfermedades:
            _logger.info("No se encontraron enfermedades")
            log_obj.create([{'tabla': 'Incapacidades', 'registro': '', 'mensaje': "No existen enfermedades"}])
            return
        
        empleados = emp_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar registros de Eleanor
        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BIncapacidades%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        incapacidades = []
        for res in respuesta:
            incapacidades.append({
                'periodo': res['periodo'],
                'id_eleanor': res['id_eleanor'],
                'codigo': res['codigo'],
                'nombre': res['nombre'],
                'motivo': res['motivo'],
                'fecha_inicio': res['fecha_inicio'],
                'fecha_fin': res['fecha_fin'],
                'folio': res['folio'],
                'adjunto': res['adjunto']
            })

        detener = False
        nuevas_incapacidades = []
        for inc in incapacidades:
            ### Buscar empleado por id de Eleanor
            emp = next((x for x in empleados if x.eleanor_id == inc['id_eleanor']), 0)

            if not emp:
                log_obj.create([{
                    'tabla': 'Incapacidades', 
                    'registro': "{}-{}-{}".format(inc['id_eleanor'], inc['codigo'], inc['nombre']),
                    'mensaje': "No se encontró el empleado"
                }])

                detener = True
                continue                

            ### Encontrar enfermedad
            enf = next((x for x in enfermedades if x.name == inc['motivo']), 0)

            if not enf:
                log_obj.create([{
                    'tabla': 'Incapacidades', 
                    'registro': inc['motivo'],
                    'mensaje': "No se encontró la enfermedad"
                }])

                detener = True
                continue

            nuevas_incapacidades.append({
                'disease_id': enf.id,
                'start_date': inc['fecha_inicio'],
                'end_date': inc['fecha_fin'],
                'folio': inc['folio'],
                'attachment_name': inc['adjunto'],
                'employee_id': emp.id,
                'company_id': id_compania 
            })

        if detener:
            _logger.info("NO SE PUEDEN CARGAR LAS INCAPACIDADES. REVISA EL LOG.")
        else:
            inc_obj.create(nuevas_incapacidades)

            _logger.info("Incapacidades creadas: {}".format(len(nuevas_incapacidades)))

################################################################################
    def CrearCambiosEstatus(self):
        _logger.info("Comienza creación de cambios de estatus")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']
        emp_obj = self.env['hr.employee']
        est_obj = self.env['hr.employee.status']
        cam_obj = self.env['pabs.eleanor.status.log']

        ### Validar que no existan registros
        cant = cam_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Cambios de estatus', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ## Consultar estatus y empleados de Odoo
        estatus = est_obj.search([
            ('id', '>', 0)
        ])
        
        empleados = emp_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar registros de Eleanor
        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BCambioEstatus%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        cambios = []
        for res in respuesta:
            cambios.append({
                'periodo': res['periodo'],
                'id_eleanor': int(res['id_eleanor']),
                'codigo': res['codigo'],
                'nombre': res['nombre'],
                'comentarios': res['comentarios'],
                'fecha': res['fecha'],
                'estatus': res['estatus'],
                'adjunto': res['adjunto']
            })

        detener = False
        nuevos_cambios = []
        for cam in cambios:

            ### Buscar empleado por id de Eleanor
            emp = next((x for x in empleados if x.eleanor_id == cam['id_eleanor']), 0)

            if not emp:
                log_obj.create([{
                    'tabla': 'Cambios de estatus', 
                    'registro': "{}-{}-{}".format(cam['id_eleanor'], cam['codigo'], cam['nombre']),
                    'mensaje': "No se encontró el empleado"
                }])

                detener = True
                continue

            ### Encontrar estatus        
            est = next((x for x in estatus if x.name == cam['estatus']), 0)

            if not est:
                log_obj.create([{
                    'tabla': 'Cambios de estatus', 
                    'registro': cam['codigo'],
                    'mensaje': "No se encontró el estatus {}".format(cam['estatus'])
                }])

                detener = True
                continue

            nuevos_cambios.append({
                'employee_status_id': est.id,
                'status_date': cam['fecha'],
                'comments': cam['comentarios'],
                'attachment_name': cam['adjunto'],
                'employee_id': emp.id,
                'company_id': id_compania 
            })

        if detener:
            _logger.info("NO SE PUEDEN CARGAR LOS CAMBIOS DE ESTATUS. REVISA EL LOG.")
        else:
            cam_obj.with_context(migration=True).create(nuevos_cambios)

            _logger.info("Cambios de estatus creados: {}".format(len(nuevos_cambios)))

################################################################################
    def CrearCategoriasConceptos(self):
        _logger.info("Comienza creación de categorias de conceptos")
        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        cat_obj = self.env['pabs.eleanor.concept.category']

        cant = cat_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Categorias de conceptos', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ### Consultar conceptos
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BConceptos%5D"
        respuesta = self.ConsultaECO_ODOO(query)

        ### Dejar un solo registro de categoria
        categorias = []
        for res in respuesta:
            if res['categoria'] not in categorias:
                categorias.append(res['categoria'])

        nuevas_categorias = []
        for cat in categorias:
            nuevas_categorias.append({
                'name': cat,
                'company_id': id_compania
            })

        cat_obj.create(nuevas_categorias)

        _logger.info("Categorias de conceptos creadas: {}".format(len(nuevas_categorias)))

################################################################################
    def CrearConceptos(self):
        _logger.info("Comienza creación de conceptos")
        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        cat_obj = self.env['pabs.eleanor.concept.category']
        conc_obj = self.env['pabs.eleanor.concept']
        acc_obj = self.env['account.account']

        ### Validar que no existan registros
        cant = conc_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Conceptos', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ### Consultar categorias de conceptos y cuentas de Odoo
        categorias = cat_obj.search([
            ('company_id', '=', id_compania)
        ])

        if not categorias:
            _logger.info("No hay categorias en Odoo")
            log_obj.create([{'tabla': 'Conceptos', 'registro': '', 'mensaje': "No hay categorias en ODOO"}])
            return

        cuentas = acc_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar conceptos
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BConceptos%5D"
        respuesta = self.ConsultaECO_ODOO(query)

        conceptos = []
        for res in respuesta:
            conceptos.append({
                'tipo': res['tipo'],
                'nombre_reducido': res['nombre_reducido'],
                'nombre_nomina': res['nombre_nomina'],
                'cuenta': res['cuenta'],
                'nombre_cuenta': res['nombre_cuenta'],
                'categoria': res['categoria'],
                'orden': int(res['orden']),
                'permitir_carga': bool(res['permitir_carga'])
            })

        detener = False
        nuevos_conceptos = []
        for conc in conceptos:
            ### Buscar id de categoria
            cat = next((x for x in categorias if x.name == conc['categoria']), 0)
            
            if not cat:
                log_obj.create([{'tabla': 'Conceptos', 'registro': conc['nombre_reducido'], 'mensaje': "No se encontró la categoria {}".format(conc['categoria']) }])
                detener = True
                continue         

            ### Buscar id de cuenta
            cuenta = next((x for x in cuentas if x.code == conc['cuenta']), 0)
            
            if not cuenta:
                log_obj.create([{'tabla': 'Conceptos', 'registro': conc['nombre_reducido'], 'mensaje': "No se encontró la cuenta {} {}".format(conc['cuenta'], conc['nombre_cuenta']) }])
                detener = True
                continue
            
            nuevos_conceptos.append({
                'name': conc['nombre_reducido'],
                'name2': conc['nombre_nomina'],
                'category_id': cat.id,
                'account_id': cuenta.id,
                'concept_type': conc['tipo'],
                'order': conc['orden'],
                'allow_load': conc['permitir_carga'],
                'company_id': id_compania
            })
            
        if detener:
            _logger.info("NO SE PUEDEN CARGAR LOS CONCEPTOS. REVISA EL LOG.")
        else:
            conc_obj.create(nuevos_conceptos)

            _logger.info("Conceptos creados: {}".format(len(nuevos_conceptos)))

################################################################################
    def CrearPeriodos(self):
        _logger.info("Comienza creación de periodos")

        id_compania = self.env.company.id
        
        log_obj = self.env['pabs.eleanor.migration.log']
        per_obj = self.env['pabs.eleanor.period']

        cant = per_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Periodos', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ### Consultar periodos
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BPeriodos%5D%20"
        respuesta = self.ConsultaECO_ODOO(query)

        periodos = []
        for res in respuesta:
            periodos.append({
                'week_number': int(res['no_periodo']),
                'date_start': res['fecha_inicial'],
                'date_end': res['fecha_final'],
                'period_type': res['tipo'],
                'state': res['estatus'],
                'company_id': id_compania
            })

        per_obj.create(periodos)

        _logger.info("Periodos creados: {}".format(len(periodos)))

################################################################################
    def CrearHistoricoSueldos(self):
        _logger.info("Comienza creación de histórico de sueldos")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']
        per_obj = self.env['pabs.eleanor.period']
        emp_obj = self.env['hr.employee']
        sue_obj = self.env['pabs.eleanor.salary.history']

        ### Validar que no existan registros
        cant = sue_obj.search_count([
            ('company_id', '=', id_compania)
        ])

        if cant > 0:
            _logger.info("Ya existen {} registros".format(cant))
            log_obj.create([{'tabla': 'Historico sueldos', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
            return

        ## Consultar periodos y empleados de Odoo
        periodos = per_obj.search([
            ('company_id', '=', id_compania)
        ])

        if not periodos:
            _logger.info("No se encontraron periodos")
            log_obj.create([{'tabla': 'Historico sueldos', 'registro': '', 'mensaje': "No existen periodos"}])
            return
        
        empleados = emp_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar registros de Eleanor
        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BHistorico_sueldos%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        sueldos_eleanor = []
        for res in respuesta:
            sueldos_eleanor.append({
                'tipo': res['tipo'],
                'no_periodo': int(res['no_periodo']),
                'fecha_inicial': res['fecha_inicial'],
                'fecha_final': res['fecha_final'],
                'id_eleanor': int(res['id_eleanor']),
                'codigo': res['codigo'],
                'nombre': res['nombre'],
                'sueldo': float(res['sueldo'])
            })

        detener = False
        nuevos_sueldos = []
        for sue in sueldos_eleanor:

            ### Buscar empleado por id de Eleanor
            emp = next((x for x in empleados if x.eleanor_id == sue['id_eleanor']), 0)

            if not emp:
                log_obj.create([{
                    'tabla': 'Historico sueldos', 
                    'registro': "{}-{}-{}".format(sue['id_eleanor'], sue['codigo'], sue['nombre']),
                    'mensaje': "No se encontró el empleado"
                }])

                detener = True
                continue

            ### Encontrar periodo
            per =   next((x for x in periodos if 
                        x.period_type == sue['tipo'] and
                        x.week_number == sue['no_periodo'] and
                        str(x.date_start) == sue['fecha_inicial'] and
                        str(x.date_end) == sue['fecha_final']
                    ), 0)
            
            if not per:
                log_obj.create([{
                    'tabla': 'Historico sueldos', 
                    'registro': "{}".format(sue['codigo']), 
                    'mensaje': "No existe el periodo {} {} {} {}".format(sue['tipo'], sue['no_periodo'], sue['fecha_inicial'], sue['fecha_final'])
                }])

                detener = True
                continue

            nuevos_sueldos.append({
                'period_id': per.id,
                'employee_id': emp.id,
                'salary': sue['sueldo'],
                'company_id': id_compania
            })

        if detener:
            _logger.info("NO SE PUEDEN CARGAR LOS HISTORICOS. REVISA EL LOG.")
        else:
            sue_obj.create(nuevos_sueldos)

            _logger.info("Históricos creados: {}".format(len(nuevos_sueldos)))

################################################################################
    def CrearMovimientos(self):
        _logger.info("Comienza migración de movimientos")

        id_compania = self.env.company.id

        log_obj = self.env['pabs.eleanor.migration.log']

        per_obj = self.env['pabs.eleanor.period']
        conc_obj = self.env['pabs.eleanor.concept']

        emp_obj = self.env['hr.employee']
        area_obj = self.env['pabs.eleanor.area']
        pue_obj = self.env['hr.job']
        dep_obj = self.env['hr.department']
        ofi_obj = self.env['stock.warehouse']

        mov_obj = self.env['pabs.eleanor.move']

        # ### Validar que no existan registros
        # cant = mov_obj.search_count([
        #     ('company_id', '=', id_compania)
        # ])

        # if cant > 0:
        #     _logger.info("Ya existen {} registros".format(cant))
        #     log_obj.create([{'tabla': 'Movimientos', 'registro': '', 'mensaje': "Ya existen {} registros".format(cant)}])
        #     return

        ## Consultar registros de Odoo
        periodos = per_obj.search([
            ('company_id', '=', id_compania)
        ])
        if not periodos:
            _logger.info("No existen periodos")
            log_obj.create([{'tabla': 'Movimientos', 'registro': '', 'mensaje': "No existen periodos"}])
            return
        
        conceptos = conc_obj.search([
            ('company_id', '=', id_compania)
        ])
        if not conceptos:
            _logger.info("No existen conceptos")
            log_obj.create([{'tabla': 'Movimientos', 'registro': '', 'mensaje': "No existen conceptos"}])
            return
        
        areas = area_obj.search([
            ('company_id', '=', id_compania)
        ])
        if not areas:
            _logger.info("No existen areas")
            log_obj.create([{'tabla': 'Movimientos', 'registro': '', 'mensaje': "No existen areas"}])
            return
        
        oficinas = ofi_obj.search([
            ('company_id', '=', id_compania),
            ('active', 'in', (True, False))
        ])

        departamentos = dep_obj.search([
            ('company_id', '=', id_compania)
        ])

        depto_ventas = next((x for x in departamentos if x.name == "VENTAS"), 0)

        if not depto_ventas:
            _logger.info("No se encontró el departamento VENTAS")
            log_obj.create([{'tabla': 'Migrar empleados', 'registro': '', 'mensaje': "No existe el departamento VENTAS"}])
            return

        puestos = pue_obj.search([
            ('company_id', '=', id_compania)
        ])

        empleados = emp_obj.search([
            ('company_id', '=', id_compania)
        ])

        ### Consultar registros de Eleanor
        _logger.info("Consultando registros en Eleanor...")

        id_base_eleanor = BASES_ELEANOR[self.env.company.name]
        query = "consulta=EXEC%20%5BELEANOR%5D.%5BMovimientos%5D%20%40id_plaza_eleanor%20%3D%20{}".format(id_base_eleanor)
        respuesta = self.ConsultaECO_ODOO(query)

        movimientos = []
        for res in respuesta:
            movimientos.append({
                'id_eleanor': int(res['id_eleanor']),
                'codigo': res['codigo'],
                'nombre': res['nombre'],
                'area': res['area'],
                'oficina': res['oficina'],
                'puesto': res['puesto'],
                'periodo_tipo': res['periodo_tipo'],
                'no_periodo': int(res['no_periodo']),
                'fecha_inicial': res['fecha_inicial'],
                'fecha_final': res['fecha_final'],
                'tipo': res['tipo'],
                'nombre_concepto': res['nombre_concepto'],
                'nombre_plantilla': res['nombre_plantilla'],
                'nombre_reducido': res['nombre_reducido'],
                'nombre_nomina': res['nombre_nomina'],
                'importe': float(res['importe'])
            })

        detener = False
        nuevos_movimientos = []

        ### Variables para porcentaje de avance (cada 5%)
        total = len(movimientos)
        porcentaje_impresion = .05
        saltos = round(total * porcentaje_impresion, 0)

        _logger.info("Validando datos de {} registros...".format(total))
        for index, mov in enumerate(movimientos, 1):

            ### Imprimir porcentaje de avance
            if index % saltos == 0:
                avance = int(round(index / total * 100, 0))
                _logger.info("{}%".format(avance))

            ### Buscar empleado por id de Eleanor
            emp = next((x for x in empleados if x.eleanor_id == mov['id_eleanor']), 0)

            if not emp:
                log_obj.create([{
                    'tabla': 'Movimientos', 
                    'registro': "{}-{}-{}-{}".format(mov['nombre_reducido'], mov['id_eleanor'], mov['codigo'], mov['nombre']),
                    'mensaje': "No se encontró el empleado"
                }])

                detener = True
                continue

            ### Encontrar periodo
            per = next((x for x in periodos if 
                        x.period_type == mov['periodo_tipo'] and
                        x.week_number == mov['no_periodo'] and
                        str(x.date_start) == mov['fecha_inicial'] and
                        str(x.date_end) == mov['fecha_final']
                    ), 0)
            
            if not per:
                log_obj.create([{
                    'tabla': 'Movimientos', 
                    'registro': "{}".format(mov['codigo']), 
                    'mensaje': "No se encontró el periodo {} {} {} {}".format(mov['periodo_tipo'], mov['no_periodo'], mov['fecha_inicial'], mov['fecha_final'])
                }])

                detener = True
                continue

            ### Encontrar concepto
            conc = next((x for x in conceptos if x.name == mov['nombre_reducido']), 0)

            if not conc:
                log_obj.create([{
                    'tabla': 'Movimientos', 
                    'registro': "{}".format(mov['codigo']), 
                    'mensaje': "No se encontró el concepto {}".format(mov['nombre_reducido'])
                }])

                detener = True
                continue
            
            ### Encontrar area
            area = next((x for x in areas if x.name == mov['area']), 0)

            if not area:
                log_obj.create([{
                    'tabla': 'Movimientos', 
                    'registro': "{}".format(mov['codigo']), 
                    'mensaje': "No se encontró el area {}".format(mov['area'])
                }])

                detener = True
                continue

            ### Encontrar puesto
            pue = next((x for x in puestos if x.name == mov['puesto']), 0)

            if not pue:
                log_obj.create([{
                    'tabla': 'Movimientos', 
                    'registro': "{}".format(mov['codigo']), 
                    'mensaje': "No se encontró el puesto {}".format(mov['puesto'])
                }])

                detener = True
                continue
            
            ### Encontrar departamento
            id_departamento = None
            id_oficina = None

            if mov['area'] == "ASISTENCIA SOCIAL":
                id_departamento = depto_ventas.id

                ### Encontrar oficina
                ofi = next((x for x in oficinas if x.name == mov['oficina']), 0)

                if ofi:
                    id_oficina = ofi.id
                else:
                    log_obj.create([{
                        'tabla': 'Movimientos', 
                        'registro': "{}".format(mov['codigo']), 
                        'mensaje': "No se encontró la oficina de ventas {}".format(mov['oficina'])
                    }])
                    detener = True
                    continue
            else:
                dep = next((x for x in departamentos if x.name == mov['oficina']), 0)

                if dep:
                    id_departamento = dep.id
                else:
                    log_obj.create([{
                        'tabla': 'Movimientos', 
                        'registro': "{}".format(mov['codigo']), 
                        'mensaje': "No se encontró el departamento {}".format(mov['oficina'])
                    }])
                    detener = True
                    continue

            ### Arreglo de nuevos movimientos
            nuevos_movimientos.append({
                'period_id': per.id,
                'move_type': mov['tipo'],
                'concept_id': conc.id,
                'employee_id': emp.id,
                'area_id': area.id,
                'job_id': pue.id,
                'amount': mov['importe'],
                'department_id': id_departamento,
                'warehouse_id': id_oficina,
                'company_id': id_compania
            })
        if detener:
            _logger.info("NO SE PUEDEN CARGAR LOS MOVIMIENTOS. REVISA EL LOG.")
        else:
            _logger.info("Creando registros en la base de datos...")

            # No crear bitácora al crear movimento
            mov_obj.with_context(migration=True).create(nuevos_movimientos)

            _logger.info("Movimientos creados: {}".format(len(nuevos_movimientos)))

################################################################################
    def MigrarAdjuntos(self, limite):
        _logger.info("Comienza migración de archivos adjuntos. LIMITE {}".format(limite))

        id_compania = self.env.company.id
        log_obj = self.env['pabs.eleanor.migration.log']
        adj_obj = self.env['ir.attachment']

        creados = 0
        no_creados = 0

        ### Migrar adjuntos de empleados ###
        consulta = """
            SELECT 
                emp.id as id_empleado,
                emp.barcode,
                emp.name,
                CASE
                    WHEN per.id IS NULL THEN emp.personal_file_name
                    ELSE ''
                END as personal_file_name,
                '' as constancy_up_name
            FROM hr_employee AS emp
            LEFT JOIN ir_attachment AS per ON emp.id = per.res_id AND per.res_model = 'hr.employee' AND per.res_field = 'personal_file_file'
                WHERE (emp.personal_file_name IS NOT NULL AND emp.personal_file_name != '' )
                AND per.id IS NULL
                AND emp.company_id = {}
            UNION SELECT 
                emp.id as id_empleado,
                emp.barcode,
                emp.name,
                '' as personal_file_name,
                CASE
                    WHEN con.id IS NULL THEN emp.constancy_up_name
                    ELSE ''
                END as constancy_up_name
            FROM hr_employee AS emp
            LEFT JOIN ir_attachment AS con ON emp.id = con.res_id AND con.res_model = 'hr.employee' AND con.res_field = 'constancy_up_file'
                WHERE (emp.constancy_up_name IS NOT NULL AND emp.constancy_up_name != '')
                AND (con.id IS NULL)
                AND emp.company_id = {}
            ORDER BY barcode
        """.format(id_compania, id_compania)

        self.env.cr.execute(consulta)

        empleados = []
        for res in self.env.cr.fetchall():
            empleados.append({
                'id_empleado': res[0],
                'barcode': res[1],
                'name': res[2],
                'personal_file_name': res[3],
                'constancy_up_name': res[4]
            })

        cantidad_empleados = len(empleados)

        _logger.info("Expedientes y constancias: {}".format(cantidad_empleados))
        for index, emp in enumerate(empleados, 1):
            if creados >= limite:
                _logger.info("Limite alcanzado")
                break


            hubo_carga = False
            if emp['personal_file_name']:
                _logger.info("{} de {}. Expediente - {} {}".format(index, cantidad_empleados, emp['barcode'], emp['name']))
                url = "http://52.27.95.193/api/adjunto?nombre={}".format(emp['personal_file_name'])
                
                respuesta = requests.get(url)

                if respuesta.text != "0":
                    archivo = respuesta.text
                    adj_obj.create({
                        'name': 'personal_file_file',
                        'type': 'binary',
                        'datas': archivo,
                        'res_model': 'hr.employee',
                        'res_field': 'personal_file_file',
                        'res_id': emp['id_empleado'],
                        'company_id': id_compania
                    })
                    hubo_carga = True
                else:
                    log_obj.create([{
                        'tabla': 'Adjuntos', 
                        'registro': "{} - expediente".format(emp['barcode'], ), 
                        'mensaje': "No se encontró el archivo {}".format(emp['personal_file_name'])
                    }])
                    no_creados = no_creados + 1

            if emp['constancy_up_name']:
                _logger.info("{} de {}. Constancia - {} {}".format(index, cantidad_empleados, emp['barcode'], emp['name']))
                url = "http://52.27.95.193/api/adjunto?nombre={}".format(emp['constancy_up_name'])
                
                respuesta = requests.get(url)

                if respuesta.text != "0":
                    archivo = respuesta.text
                    adj_obj.create({
                        'name': 'constancy_up_file',
                        'type': 'binary',
                        'datas': archivo,
                        'res_model': 'hr.employee',
                        'res_field': 'constancy_up_file',
                        'res_id': emp['id_empleado'],
                        'company_id': id_compania
                    })
                    hubo_carga = True
                else:
                    log_obj.create([{
                        'tabla': 'Adjuntos', 
                        'registro': "{} - constancia".format(emp['barcode'], ), 
                        'mensaje': "No se encontró el archivo {}".format(emp['constancy_up_name'])
                    }])
                    no_creados = no_creados + 1

            if hubo_carga:
                creados = creados + 1

        ### Migrar adjuntos de cambios de estatus ###
        consulta = """
            SELECT 
                cam.id as id_cambio,	
                emp.barcode,
                emp.name,
                CASE
                    WHEN adj.id IS NULL THEN cam.attachment_name
                    ELSE ''
                END as attachment_name
            FROM hr_employee AS emp
            INNER JOIN pabs_eleanor_status_log AS cam ON emp.id = cam.employee_id
            LEFT JOIN ir_attachment AS adj ON cam.id = adj.res_id AND adj.res_model = 'pabs.eleanor.status.log' AND adj.res_field = 'attachment_file'
                WHERE (cam.attachment_name IS NOT NULL AND cam.attachment_name != '')
                AND adj.id IS NULL
                AND emp.company_id = {}
                    ORDER BY emp.barcode
        """.format(id_compania)

        self.env.cr.execute(consulta)

        cambios = []
        for res in self.env.cr.fetchall():
            cambios.append({
                'id_cambio': res[0],
                'barcode': res[1],
                'name': res[2],
                'attachment_name': res[3]
            })

        cantidad_cambios = len(cambios)

        _logger.info("Adjuntos de cambios: {}".format(cantidad_cambios))
        for index, cam in enumerate(cambios, 1):
            if creados >= limite:
                _logger.info("Limite alcanzado")
                break

            _logger.info("{} de {}. {} {}".format(index, cantidad_cambios, cam['barcode'], cam['name']))
        
            if cam['attachment_name']:
                _logger.info("Cambios de estatus")
                url = "http://52.27.95.193/api/adjunto?nombre={}".format(cam['attachment_name'])
                
                respuesta = requests.get(url)

                if respuesta.text != "0":
                    archivo = respuesta.text
                    adj_obj.create({
                        'name': 'attachment_file',
                        'type': 'binary',
                        'datas': archivo,
                        'res_model': 'pabs.eleanor.status.log',
                        'res_field': 'attachment_file',
                        'res_id': cam['id_cambio'],
                        'company_id': id_compania
                    })
                    creados = creados + 1
                else:
                    log_obj.create([{
                        'tabla': 'Adjuntos', 
                        'registro': "{} - cambios de estatus".format(cam['barcode'], ), 
                        'mensaje': "No se encontró el archivo {}".format(cam['attachment_name'])
                    }])
                    no_creados = no_creados + 1

        ### Migrar adjuntos de incapacidades ###
        consulta = """
            SELECT 
                inc.id as id_incapacidad,
                emp.barcode,
                emp.name,
                CASE
                    WHEN adj.id IS NULL THEN inc.attachment_name
                    ELSE ''
                END as attachment_name
            FROM hr_employee AS emp
            INNER JOIN pabs_eleanor_inability AS inc ON emp.id = inc.employee_id
            LEFT JOIN ir_attachment AS adj ON inc.id = adj.res_id AND adj.res_model = 'pabs.eleanor.inability' AND adj.res_field = 'attachment_file'
                WHERE (inc.attachment_name IS NOT NULL AND inc.attachment_name != '')
                AND adj.id IS NULL
                AND emp.company_id = {}
                    ORDER BY emp.barcode
        """.format(id_compania)

        self.env.cr.execute(consulta)

        incapacidades = []
        for res in self.env.cr.fetchall():
            incapacidades.append({
                'id_incapacidad': res[0],
                'barcode': res[1],
                'name': res[2],
                'attachment_name': res[3]
            })

        cantidad_incapacidades = len(incapacidades)

        _logger.info("Adjuntos de incapacidades {}".format(cantidad_incapacidades))
        for index, inc in enumerate(incapacidades, 1):
            if creados >= limite:
                _logger.info("Limite alcanzado")
                break

            _logger.info("{} de {}. {} {}".format(index, cantidad_incapacidades, inc['barcode'], inc['name']))
        
            if inc['attachment_name']:
                _logger.info("Incapacidad")
                url = "http://52.27.95.193/api/adjunto?nombre={}".format(inc['attachment_name'])
                
                respuesta = requests.get(url)

                if respuesta.text != "0":
                    archivo = respuesta.text
                    adj_obj.create({
                        'name': 'attachment_file',
                        'type': 'binary',
                        'datas': archivo,
                        'res_model': 'pabs.eleanor.inability',
                        'res_field': 'attachment_file',
                        'res_id': inc['id_incapacidad'],
                        'company_id': id_compania
                    })
                    creados = creados + 1
                else:
                    log_obj.create([{
                        'tabla': 'Adjuntos', 
                        'registro': "{} - incapacidad".format(inc['barcode'], ), 
                        'mensaje': "No se encontró el archivo {}".format(inc['attachment_name'])
                    }])
                    no_creados = no_creados + 1

        _logger.info("Adjuntos >>> Creados: {}. No creados :{}".format(creados, no_creados))