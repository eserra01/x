# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from num2words import num2words

class MortuaryReceipt(models.AbstractModel):
    _name="report.mortuary.receipt"

    @api.model
    def _get_report_values(self, docids, data=None):

        if len(docids) > 1:
            raise ValidationError("Se recibió mas de un pago para la impresión del recibo. ids: {}".format(docids))

        #Objeto pago
        payment_obj = self.env['account.payment'].search([('id','=',docids)])

        if not payment_obj:
            raise ValidationError("No se encontró el pago para el id {}".format(docids))

        #Objeto bitácora
        mortuary_obj = self.env['mortuary'].search([('name','=',payment_obj.binnacle.name), ('company_id','=', self.env.company.id)])
        if not mortuary_obj:
            raise ValidationError("No se encontró la referencia a la bitácora {} en el pago".format(payment_obj.binnacle.name))

        if  len(mortuary_obj) > 1:
            raise ValidationError("Se encontró mas ".format(payment_obj.binnacle.name))

        #Datos de encabezado por compañia
        encabezado = []
        if self.env.company.id == 7: #CUERNAVACA
            encabezado.append("CALLE: FRANCISCO I. MADERO No. 719, COL.")
            encabezado.append("MIRAVAL, CP. 62270, DELEGACION BENITO")
            encabezado.append("JUAREZ, CUERNAVACA, MORELOS")
            encabezado.append("BETZABE DELGADO GALBILLO")
            encabezado.append("RFC DEGB-820517-3T5")
            encabezado.append("CURP. DEGB820317MNTLLT07")
            encabezado.append("TEL. 01(777) 170 4870")
        if self.env.company.id == 1: #ACAPULCO
            encabezado.append("Calle Vasco Núñez de Balboa, ")
            encabezado.append("Fracc: Hornos No 3. CP: 39350")
            encabezado.append("Acapulco, Gro")
            encabezado.append("ABELARDO AHUMADA RANGEL")
            encabezado.append("RFC AURORA -781005-TL3")
            encabezado.append("CURP. AURA781005HNTHNB09")
            encabezado.append("Teléfono: 3310418052")

        cuerpo = {
            'bitacora': mortuary_obj.name,
            'contrato': mortuary_obj.tc_no_contrato,
            'recibo': payment_obj.name,
            'fecha_recibo': payment_obj.payment_date,
            'cliente': payment_obj.payment_person,
            'finado': mortuary_obj.ii_finado,
            'lugar_fallecimiento': payment_obj.place_of_death,
            'fecha_defuncion': payment_obj.date_of_death,
            'cantidad': payment_obj.amount,
            'cantidad_letra': self.env.user.company_id.currency_id.amount_to_text(payment_obj.amount),
            'adicionales': payment_obj.additional,
            'autor': self.env.user.name,
            'cajera': payment_obj.user_create_payment.name
        }

        return {
            'encabezado': encabezado,
            'cuerpo': cuerpo
        }