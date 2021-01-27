# -*- coding: utf-8 -*-

from odoo.addons.pabs_custom.externals.calcule import CalculeRFC, CalculeCURP, CalculeGeneric

class GenerateDataFiscal(CalculeGeneric):
	generadores = (CalculeCURP, CalculeRFC)



datos = {
	'fecha': 'value', 'nombres': 'value', 'paterno': 'value',
	'materno': None, 'genero': 'value', 'estado': 'value'
}

#Solo cálcula RFC.
rfc = CalculeRFC(nombres='@param', paterno='@param', materno='@param', fecha='@param').data
print(rfc)
#Solo cálcula CURP.
curp = CalculeCURP(**datos).data
print(curp)
#Calcula RFC y CURP.
todo = GenerateDataFiscal(**datos).data
print(todo)
