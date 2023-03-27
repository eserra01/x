# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsCompanies(models.Model):
    _name = 'pabs.companies'
    _description = 'Razones sociales'

    name = fields.Char(string = 'Razón social', required = True)
    company_id = fields.Many2one('res.company', string = 'Compañia', required=True, default=lambda s: s.env.company.id)

    _sql_constraints = [
        (
            'unique_companies_record',
            'UNIQUE(name, company_id)',
            'No se puede crear el registro: ya existe esa razon social'
        ),
    ]
    
class PabsCompaniesByContract(models.Model):
    _name = 'pabs.companies.by.contract'
    _description = 'Razon social por plan'
    _rec_name = 'prefix_contract'

    prefix_contract = fields.Char(string ='Serie del contrato', required=True)
    pabs_company = fields.Many2one(comodel_name = 'pabs.companies', string = 'Empresa', required=True)
    company_id = fields.Many2one(comodel_name = 'res.company', string = 'Compañia', required=True, default=lambda s: s.env.company.id)

    def contar_contratos(self):
        id_compania = self.env.company.id

        ### Obtener razones sociales por prefijo
        razones = self.search([
            ('company_id', '=', id_compania)
        ])

        ### Ordenar para evaluar las opciones mas específicas primero
        razones = razones.sorted(key = lambda x: len(x.prefix_contract), reverse = True)

        ### Obtener la cantidad de contratos por prefijo
        consulta = """
            SELECT 
                CASE
                    WHEN name ~ '^[0-9]' 			THEN SUBSTRING(name, 1, 3) /*serie de 3 caracteres*/
                    WHEN name ~ '^[A-Z][A-Z][0-9]' 	THEN SUBSTRING(name, 1, 2) /*serie de 2 caracteres*/
                    WHEN name ~ '^[A-Z][0-9]' 		THEN SUBSTRING(name, 1, 1) /*serie de 1 caracter*/
                    ELSE name
                END as prefijo,
                COUNT(*)
            FROM pabs_contract
                WHERE state = 'contract'
                AND company_id = {}
                    GROUP BY 1
        """.format(id_compania)

        self.env.cr.execute(consulta)

        lista_contratos = []
        for res in self.env.cr.fetchall():
            lista_contratos.append({
                'prefijo': res[0],
                'cantidad': int(res[1])
            })

        ### Calcular cantidad de contratos por razon social
        msj = "Cantidad de contratos por regla:\n"
        for raz in razones:
            contratos = list((x for x in lista_contratos if raz.prefix_contract in x['prefijo']))

            if contratos:
                cantidad = 0
                for con in contratos:
                    cantidad = cantidad + con['cantidad']
                    lista_contratos.remove(con)

                msj += "{}: {}\n".format(raz.prefix_contract, cantidad)
            else:
                msj += "{}: 0\n".format(raz.prefix_contract)
        
        if lista_contratos:
            msj += "\nPrefijos de contratos sin regla:\n"
            for con in lista_contratos:
                msj += "{}: {}\n".format(con['prefijo'], con['cantidad'])

        raise ValidationError(msj)

    _sql_constraints = [
        (
            'unique_companies_by_contract_record',
            'UNIQUE(prefix_contract, company_id)',
            'No se puede crear el registro: ya existe ese prefijo'
        ),
    ]

    ### VERSION ANTERIOR
    # @api.model
    # def create(self, values):

        # consulta = """
        #     SELECT 
        #         con.prefijo
        #     FROM
        #     (
        #         SELECT 
        #             DISTINCT CASE
        #                 WHEN name ~ '^[0-9]' 			THEN SUBSTRING(name, 1, 3) /*serie de 3 caracteres*/
        #                 WHEN name ~ '^[A-Z][A-Z][0-9]' 	THEN SUBSTRING(name, 1, 2) /*serie de 2 caracteres*/
        #                 WHEN name ~ '^[A-Z][0-9]' 		THEN SUBSTRING(name, 1, 1) /*serie de 1 caracter*/
        #                 ELSE name
        #             END as prefijo
        #         FROM pabs_contract
        #             WHERE state = 'contract'
        #             AND company_id = {}
        #     ) AS con
        #     LEFT JOIN pabs_companies_by_contract AS raz ON con.prefijo = raz.prefix_contract
        #         WHERE raz.id IS NULL
        # """.format(self.env.company.id)
        
    #     self.env.cr.execute(consulta)

    #     prefijos = []
    #     for res in self.env.cr.fetchall():
    #         prefijos.append(res[0])

    #     if values['prefix_contract'] not in prefijos:
    #         raise ValidationError("El prefijo no es válido, los valores posibles son {}".format(prefijos))

    #     res = super(PabsCompaniesByContract,self).create(values)
    #     return res