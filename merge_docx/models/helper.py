# -*- coding: utf-8 -*-
import time
from reportlab.graphics.barcode import createBarcodeDrawing
import base64
from datetime import date
from pytz import timezone
from odoo.tools import wrap_module

import datetime

# build dateutil helper, starting with the relevant *lazy* imports
import dateutil
import dateutil.parser
import dateutil.relativedelta
import dateutil.rrule
import dateutil.tz
mods = {'parser', 'relativedelta', 'rrule', 'tz'}
attribs = {atr for m in mods for atr in getattr(dateutil, m).__all__}
dateutil = wrap_module(dateutil, mods | attribs)
from odoo.tools.translate import _


def barcode(barcode_type, value, width=600, height=100, humanreadable=0, quiet=1):
    """Contoller able to render barcode images thanks to reportlab.
    Samples:
    py3o.image(barcode('QR', o.name, width=100, height=100), 'png', width='3cm', height='3cm', isb64=True)
        
    :param barcode_type: Accepted types: 'Codabar', 'Code11', 'Code128', 'EAN13', 'EAN8', 'Extended39',
    'Extended93', 'FIM', 'I2of5', 'MSI', 'POSTNET', 'QR', 'Standard39', 'Standard93',
    'UPCA', 'USPS_4State'
    :param humanreadable: Accepted values: 0 (default) or 1. 1 will insert the readable value
    at the bottom of nthe output image
    :param quiet: Accepted values: 0 (default) or 1. 1 will display white
    margins on left and right.
    """

    if barcode_type == 'UPCA' and len(value) in (11, 12, 13):
        barcode_type = 'EAN13'
        if len(value) in (11, 12):
            value = '0%s' % value
    width, height, humanreadable, quiet = int(width), int(height), bool(int(humanreadable)), bool(int(quiet))
    try:
        barcode = createBarcodeDrawing(
            barcode_type, value=value, format='png', width=width, height=height,
            humanReadable=humanreadable, quiet=quiet
        )
        # return barcode.asString('png') => remove param isb64
        return base64.b64encode(barcode.asString('png')) # isb64=True
    except (ValueError, AttributeError):
        if barcode_type == 'Code128':
            raise ValueError("Cannot convert into barcode.")
        else:
            barcode = createBarcodeDrawing(
                'Code128', value=value, format='png', width=width, height=height,
                humanReadable=humanreadable, quiet=quiet
            )
            return base64.b64encode(barcode.asString('png'))


def extra_global_vals(env):
    # https://www.htmlsymbols.xyz/miscellaneous-symbols/ballot-box-symbols
    company = env.user.company_id

    def _t(name):
        trad = env['ir.translation']._get_source(name, ('code',), env.context.get('lang', 'en_US'))
        if trad:
            return trad
        else:
            return env['ir.translation']._get_source_name(name, ('code',), env.context.get('lang', 'en_US'))

    return {
        'user': env.user, 'company_id': company, 'lang': env.lang, 'time': time, 'env': env, 'date': date,
        'timezone': timezone, 'datetime': datetime, 'dateutil': dateutil,
        'company_vat_label': company.vat_label, 'company_vat_label_full': company.vat_label_full,
        'company_display_address': company.partner_id.display_address,
        'company_name': company.name,
        'company_footer_line': company.footer_line,
        'company_footer_line_break': company.footer_line_break,
        'company_footer_line_icon': company.footer_line_icon,
        'company_footer_line_break_icon': company.footer_line_break_icon,
        'company_header': company.report_header,
        'company_footer': company.report_footer,
        # Icons
        # https://www.fileformat.info/info/unicode/char/1f4de/index.htm
        'iphone': '\U0001F4DE',
        # https://www.fileformat.info/info/unicode/char/1f4f1/index.htm
        'imobile': '\U0001F4F1',
        # https://www.fileformat.info/info/unicode/char/2709/index.htm
        'iemail': '\u2709',
        # https://www.fileformat.info/info/unicode/char/1f310/index.htm
        'iwebsite': '\U0001f310',
        # https://www.utf8icons.com/character/128176/money-bag
        'imoney': '\U0001F4B0',
        # https://www.utf8icons.com/character/128181/banknote-with-dollar-sign
        'idolar': '\U0001F4B5',
        # https://www.utf8icons.com/character/127991/label
        'ilabel': '\U0001F3F7',
        # https://www.utf8icons.com/character/128456/note
        'inote': '\U0001F5C8',
        # https://www.utf8icons.com/character/128437/screen
        'iimg': '\U0001F5B5',
        # https://www.utf8icons.com/character/9776/trigram-for-heaven
        'ilist': '\u2630',
        # https://www.utf8icons.com/character/9783/trigram-for-earth
        'iqty': '\u2637',
        # https://graphemica.com/%F0%9F%93%8C
        'ipushpin': '\U0001F4CC',
        # https://www.compart.com/en/unicode/U+1F3E2
        'ioffice': '\U0001F3E2',
        'barcode': barcode,
        '_t': _t,
        '_': _,
    }
