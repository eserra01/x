# -*- coding: utf-8 -*-

from xml.dom import ValidationErr
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AddBalanceWizard(models.TransientModel):
  _name = 'add.balance.wizard'
  _description = 'Aumentar saldo en contrato'

  amount = fields.Float(string="Saldo a aumentar", default=0)
  reason = fields.Char(string="Motivo", default='')

  def add_balance_action(self):
    # 
    if self.amount <= 0:
      raise ValidationError("El monto debe ser mayor que cero.")
    #
    contract_id = self.env['pabs.contract'].browse(self.env.context.get('active_id'))
    if contract_id:
      # 
      product_id = self.env['product.product'].search([('name','=','PENALIZACION POR REACTIVACION'),('company_id','=',contract_id.company_id.id)])
      if not product_id:
        raise ValidationError("No se encuentra el producto PENALIZACION POR REACTIVACION")
      account_id = product_id.product_tmpl_id.property_account_income_id or product_id.product_tmpl_id.categ_id.property_account_income_categ_id
      if not account_id:
        raise ValidationError("No se encuentra la cuenta de ingresos en el producto o su categoría.")
      journal_id = self.env['account.journal'].search([('name','=','VENTAS'),('company_id','=',contract_id.company_id.id)])
      if not journal_id:
        raise ValidationError("No se encuentra el diario de VENTAS")
      currency_id = self.env['account.move'].with_context(default_type='out_invoice')._get_default_currency()     
      if not currency_id:
        raise ValidationError("No se encuentra la moneda de la compañia")
      account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)

      factor_iva = 0
      ### FISCAL: Validar registros de impuestos
      if contract_id.company_id.apply_taxes:
        #Buscar impuesto a agregar
        iva_tax = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', contract_id.company_id.id)])
        
        if not iva_tax:
          raise ValidationError("No se encontró el impuesto con nombre IVA")

        #Buscar linea de repartición de impuesto para facturas
        iva_repartition_line = iva_tax.invoice_repartition_line_ids.filtered_domain([
          ('repartition_type','=','tax'), 
          ('invoice_tax_id','=', iva_tax.id), 
          ('company_id','=', contract_id.company_id.id)
        ])

        if not iva_repartition_line:
          raise ValidationError("No se encontró la repartición de facturas del impuesto {}".format(iva_tax.name))
        if len(iva_repartition_line) > 1:
          raise ValidationError("Se definió mas de una linea (sin incluir la linea base) en la repartición de facturas del impuesto {}".format(iva_tax.name))

        factor_iva = 1 + (iva_tax.amount/100)

      ### Encabezado de la factura
      data = {
        'date' : fields.Date.context_today(self),
        'commercial_partner_id' : contract_id.partner_id.id,
        'partner_id' : contract_id.partner_id.id,
        'ref' : contract_id.full_name,
        'type' : 'out_invoice',
        'journal_id' : journal_id.id,
        'state' : 'draft',
        'currency_id' : currency_id.id,
        'invoice_date' : fields.Date.context_today(self),
        'auto_post' : False,
        'contract_id' : contract_id.id,
        'invoice_user_id' : self.env.user.id,
      }
      invoice_id = self.env['account.move'].create(data)

      if invoice_id:
        ### Linea de crédito
        credit_line = {
          'move_id' : invoice_id.id,
          'account_id' : account_id.id,
          'quantity' : 1,
          'price_unit' : self.amount,
          'credit' : self.amount,
          'product_uom_id' : product_id.product_tmpl_id.uom_id.id,
          'partner_id' : contract_id.partner_id.id,
          'amount_currency' : 0,
          'product_id' : product_id.id,
          'is_rounding_line' : False,
          'exclude_from_invoice_tab' : False,
          'name' : product_id.product_tmpl_id.description_sale or product_id.name,
        }

        ### FISCAL: Actualizar datos de línea de crédito
        if contract_id.company_id.apply_taxes:
          credit_line.update({
            'credit' : round(self.amount / factor_iva, 2),
            'tax_exigible' : True,
            'tax_ids' : [(4, iva_tax.id, 0)]
          })

        account_line_obj.create(credit_line)

        ### FISCAL: Crear línea de crédito para IVA
        if contract_id.company_id.apply_taxes:
          #Llenar datos para línea de IVA
          iva_data = {
            'move_id' : invoice_id.id,
            'account_id' : iva_repartition_line.account_id.id,
            'quantity' : 1,
            'credit' : round(self.amount - round( self.amount / factor_iva, 2), 2),
            'tax_base_amount' : round(self.amount - round( self.amount / factor_iva, 2), 2),
            'partner_id' : contract_id.partner_id.id,
            'amount_currency' : 0,
            'is_rounding_line' : False,
            'exclude_from_invoice_tab' : True,
            'tax_exigible' : False,
            'name' : iva_tax.name,
            'tax_line_id' : iva_tax.id,
            'tax_group_id' : iva_tax.tax_group_id.id,
            'tax_repartition_line_id' : iva_repartition_line.id,
          }

          account_line_obj.create(iva_data)

        ### Linea de débito
        debit_line = {
          'move_id' : invoice_id.id,
          'account_id' : invoice_id.partner_id.property_account_receivable_id.id,
          'quantity' : 1,
          'date_maturity' : fields.Date.context_today(self),
          'amount_currency' : -self.amount,
          'partner_id' : contract_id.partner_id.id,
          'tax_exigible' : False,
          'is_rounding_line' : False,
          'exclude_from_invoice_tab' : True,
          #'price_unit' : (costo * -1),
          'debit' : self.amount,
        }

        account_line_obj.create(debit_line)

        ### Aumentar comision de Fideicomiso
        arbol_fideicomiso = self.env['pabs.comission.tree'].search([
          ('contract_id.id', '=', contract_id.id),
          ('job_id.name', '=', 'FIDEICOMISO')
        ])

        if not arbol_fideicomiso:
          raise ValidationError("El contrato no tiene la rama FIDEICOMISO en su árbol de comisiones")
        
        if len(arbol_fideicomiso) > 1:
          raise ValidationError("El contrato tiene mas de una rama FIDEICOMISO en su árbol de comisiones")

        ### FISCAL: Aumentar comision de IVA y Fideicomiso
        if contract_id.company_id.apply_taxes:
          arbol_iva = self.env['pabs.comission.tree'].search([
            ('contract_id.id', '=', contract_id.id),
            ('job_id.name', '=', 'IVA')
          ])

          if not arbol_iva:
            raise ValidationError("El contrato no tiene la rama IVA en su árbol de comisiones")
          
          if len(arbol_iva) > 1:
            raise ValidationError("El contrato tiene mas de una rama IVA en su árbol de comisiones")
          
          arbol_fideicomiso.write({
            'corresponding_commission': arbol_fideicomiso.corresponding_commission + round(self.amount / factor_iva, 2),
            'remaining_commission': arbol_fideicomiso.remaining_commission + round(self.amount / factor_iva, 2)
          })

          arbol_iva.write({
            'corresponding_commission': arbol_iva.corresponding_commission + round(self.amount - round( self.amount / factor_iva, 2), 2),
            'remaining_commission': arbol_iva.remaining_commission + round(self.amount - round( self.amount / factor_iva, 2), 2)
          })

        else:
          arbol_fideicomiso.write({
            'corresponding_commission': arbol_fideicomiso.corresponding_commission + self.amount,
            'remaining_commission': arbol_fideicomiso.remaining_commission + self.amount
          })

        ### Finalizar creación de la factura
        invoice_id.action_post()
        contract_id.message_post(body="Se creó la factura {} para aumentar el saldo del contrato por el suguiente motivo: \n{}".format(invoice_id.name,self.reason))
      else:
        raise ValidationError("Error al crear la factura.")
    else:
      raise ValidationError("No se encuentra el contrato especificado.")
    return True