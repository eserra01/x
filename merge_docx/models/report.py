# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from base64 import standard_b64decode
from PyPDF2 import PdfFileWriter, PdfFileReader
import tempfile
import io
from subprocess import Popen, PIPE
import time

from odoo import models, fields, api
import odoo
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import find_in_path
from odoo.exceptions import ValidationError
from .helper import extra_global_vals

import pprint
from .mailmerge import MailMerge
from operator import itemgetter
import itertools
from odoo.tools.misc import formatLang, format_date
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

import logging
import sys
from imp import reload

_logger = logging.getLogger(__name__)

if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("utf-8")


def format_user_tz(self):
    lang = self._context.get("lang")
    record_lang = self.env["res.lang"].with_context({'not_recursion': True}).search([("code", "=", lang)], limit=1)
    if record_lang:
        datetime_format = "%s %s" % (record_lang.date_format, record_lang.time_format)
        date_format = record_lang.date_format
    else:
        datetime_format = DEFAULT_SERVER_DATETIME_FORMAT
        date_format = DEFAULT_SERVER_DATE_FORMAT
    user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
    return datetime_format, date_format, user_tz


class Dict2Class(object):
    def __init__(self, my_dict):
        for key in my_dict:
            setattr(self, key, my_dict[key])


MIME_DICT = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}

OUTPUT_FILE = [("docx", "docx"), ("pdf", "pdf")]


def compile_file(cmd):
    try:
        compiler = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    except Exception:
        msg = "Could not execute command %r" % cmd[0]
        _logger.error(msg)
        return ''
    result = compiler.communicate()
    if compiler.returncode:
        error = result
        _logger.warning(error)
        return ''
    return result[0]


def get_command(format_out, file_convert):
    try:
        unoconv = find_in_path('unoconv')
    except IOError:
        unoconv = 'unoconv'
    return [unoconv, "--stdout", "-f", "%s" % format_out, "%s" % file_convert]


class BFExtend(models.AbstractModel):
    _name = 'bf.extend'

    template_docx_id = fields.Many2one("ir.attachment", "Template *.docx", domain=[('type', '=', 'binary')])
    template_output_extension = fields.Selection(
        OUTPUT_FILE,
        string="Output extension",
        help='Output extension (Format Default *.docx Output File)'
    )
    template_output_file = fields.Binary(string='Output file')
    template_output_file_name = fields.Char(string='Output file name')
    merge_report = fields.Boolean(string="Merge report")
    report_html = fields.Html(string="HTML")

    def bf_render(self, record=None, tmpl_docx=None, data={}, output_file='docx'):
        # Call from other object context lang
        # with_context(lang=lang).bf_render(params)
        if not tmpl_docx:
            return None, None
        in_stream = io.BytesIO(standard_b64decode(tmpl_docx))
        document = MailMerge(in_stream)
        fields_template = document.get_merge_fields()
        data = self.docx_values(record, fields_template)
        temp = tempfile.NamedTemporaryFile()

        document.merge(**data)
        document.write(temp)
        temp.seek(0)
        default_out_docx = temp.read()
        if output_file == 'docx':
            temp.close()
            return default_out_docx, "docx"
        out = compile_file(get_command(output_file, temp.name))
        temp.close()
        if not out:
            return default_out_docx, "docx"
        return out, output_file

    def list_pdf(self):
        # Return list pdfs
        out, output_file = self.bf_render(record=self, tmpl_docx=self.template_docx_id.datas, output_file='pdf')
        if out:
            if output_file == 'pdf':
                pdf_content_stream = io.BytesIO(out)
                return [pdf_content_stream]
        return []


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    report_type = fields.Selection(
        selection_add=[('docx', 'DOCX')])
    template_id = fields.Many2one("ir.attachment", "Template *.docx")
    output_file = fields.Selection(
        OUTPUT_FILE,
        string='Format Output File.',
        default='docx',
        help='Format Output File. (Format Default *.docx Output File)'
    )
    url_theme_screenshot = fields.Char(string='URL theme screenshot')
    merge_pdf = fields.Boolean(string='Merge pdf', help='Merge pdf with template_docx_id')
    merge_template_id = fields.Many2one(
        "ir.actions.report", string='Merge template', help='Merge template type qweb-pdf')

    def render(self, res_ids, data=None):
        report_type = self.report_type.lower().replace('-', '_')
        if 'docx' == report_type:
            mimetype, out, report_name, ext = self.render_any_docs(res_ids, data=data)
            return out, ext
        else:
            return super(IrActionsReport, self).render(res_ids, data)

    @api.model
    def docx_values(self, doc, fields_template):
        # Return fields values
        data = {}
        def get_object_value(obj, template_field):
            split_exp = template_field.split('.')
            for i, tfield in enumerate(split_exp):
                # How to know if an object has an attribute
                if hasattr(obj, tfield):
                    field_type = obj._fields[tfield].type
                    if field_type == 'many2one':
                        obj = getattr(obj, tfield)
                        continue
                    elif field_type == 'date':
                        if not split_exp[i+1:]:
                            obj = format_date(obj.env, getattr(obj, tfield))
                        else:
                            obj = getattr(obj, tfield)
                    elif field_type == 'datetime':
                        if not split_exp[i+1:]:
                            datetime_format, date_format, user_tz = format_user_tz(obj)
                            obj = getattr(obj, tfield)
                            def format_datetime(dt_attendance):
                                if dt_attendance:
                                    return fields.Datetime.from_string(dt_attendance).replace(
                                        tzinfo=pytz.utc
                                    ).astimezone(user_tz).strftime(datetime_format)
                                else:
                                    return ''
                            obj = format_datetime(obj)
                        else:
                            obj = getattr(obj, tfield)
                    elif field_type == 'selection':
                        obj = dict(obj._fields[tfield]._description_selection(obj.env)).get(getattr(obj, tfield))
                    elif field_type == 'monetary':
                        obj = formatLang(obj.env, getattr(obj, tfield), currency_obj=obj.currency_id)
                    elif field_type == 'boolean':
                        # Ref. https://www.htmlsymbols.xyz/miscellaneous-symbols/ballot-box-symbols
                        if getattr(obj, tfield):
                            # https://www.htmlsymbols.xyz/unicode/U+2611
                            # obj = u"☑"
                            obj = "\u2611"
                        else:
                            # https://www.htmlsymbols.xyz/unicode/U+2610
                            # obj = u"☐"
                            obj = "\u2610"
                    elif field_type == 'float':
                        if not split_exp[i+1:]:
                            if obj._fields[tfield].get_digits(obj.env):
                                precision, scale = obj._fields[tfield].get_digits(obj.env)
                                obj = formatLang(obj.env, getattr(obj, tfield), digits=scale)
                            else:
                                obj = getattr(obj, tfield)
                        else:
                            obj = getattr(obj, tfield)
                    elif field_type == 'char':
                        obj = getattr(obj, tfield) or ''
                    elif field_type == 'one2many' or field_type == 'many2many':
                        obj = getattr(obj, tfield)
                        one2many_split = ".".join(split_exp[:i+1])
                        obj = [{'field_one2many': one2many_split, 'line': line.id, 'col_val': {'o.' + template_field: get_object_value(line, ".".join(split_exp[i+1:]))}} for line in obj]
                        break
                    else:
                        obj = getattr(obj, tfield)
                    # Execute attrs
                    if split_exp[i+1:]:
                        if obj:
                            eval_context = {'obj': obj}
                            obj = safe_eval('obj' + '.' + ('.'.join(split_exp[i+1:])), eval_context)
                            break
                        else:
                            obj = ''
                            break
                else:
                    if tfield.split('bf_label_')[1:]:
                        # Print label
                        tfield, = tfield.split('bf_label_')[1:]
                        if hasattr(obj, tfield):
                            obj = obj._fields[tfield]._description_string(obj.env)
                            # Execute attrs
                            if split_exp[i+1:]:
                                if obj:
                                    eval_context = {'obj': obj}
                                    obj = safe_eval('obj' + '.' + ('.'.join(split_exp[i+1:])), eval_context)
                                    break
                                else:
                                    obj = ''
                                    break
                        else:
                            # Genera el error para constatar que objeto no tiene atributo
                            getattr(obj, tfield)
                    else:
                        if tfield[:3] == 'bf_':
                            tfield = tfield.split('bf_')[1]
                            # How to know if an object has an attribute
                            if hasattr(obj, tfield):
                                field_type = obj._fields[tfield].type
                                if field_type == 'many2many':
                                    obj = ", ".join([o.display_name for o in getattr(obj, tfield)])
                                # Execute attrs
                                if split_exp[i+1:]:
                                    if obj:
                                        eval_context = {'obj': obj}
                                        obj = safe_eval('obj' + '.' + ('.'.join(split_exp[i+1:])), eval_context)
                                        break
                                    else:
                                        obj = ''
                                        break
                            else:
                                # Genera el error para constatar que objeto no tiene atributo
                                getattr(obj, tfield)
                        else:
                            # Genera el error para constatar que objeto no tiene atributo
                            getattr(obj, tfield)
            return obj

        lang = self.env.user.lang or 'en_US'

        # Clasification fields, expression
        obj_fields = []
        expressions = []
        for field in fields_template:
            # o.* record extend Odoo for report template docx
            if field == 'o':
                # Key return obj
                obj_fields.append(field)
            else:
                if field[:2] == "o.":
                    obj_fields.append(field)
                else:
                    expressions.append(field)

        if hasattr(doc, 'context_lang'):
            lang = doc.context_lang() or lang
        eval_context = extra_global_vals(self.env(context=dict(self.env.context, lang=lang)))

        # Add context
        # For translate example: _('Sale Order')
        eval_context.update({'context': dict(self.env.context, lang=lang)})
        # Record Odoo
        eval_context.update({'record': doc})

        # The merge_docx_extend method must return a dictionary
        # If any model has method merge_docx_extend
        if hasattr(doc, 'merge_docx_extend'):
            eval_context.update({"data": Dict2Class(doc.with_context(lang=lang).merge_docx_extend())})

        for template_field in obj_fields:
            if template_field == "o":
                # Return key: obj
                data.update({template_field: doc})
            else:
                val = get_object_value(doc, template_field[2:])
                data.update({template_field: val})

        one2many_list = []
        keys_pop = []
        for key in data:
            # Only one2many, many2many fields
            if type(data[key]) == list:
                one2many_list += data[key]
                keys_pop.append(key)

        # Remove keys one2many, many2many
        for key in keys_pop: data.pop(key)

        # Group one2many, many2many
        sorted_one2many_list = sorted(one2many_list, key=itemgetter('field_one2many'))
        group_one2many = [list(items) for key, items in itertools.groupby(sorted_one2many_list, key=lambda x:x['field_one2many'])]
        for one2many in group_one2many:
            sorted_one2many_list = sorted(one2many, key=itemgetter('line'))
            group_line = [list(items) for key, items in itertools.groupby(sorted_one2many_list, key=lambda x:x['line'])]
            lines = []
            for line in group_line:
                val = {}
                for i in line:
                    val.update(i['col_val'])
                lines.append(val)
            # Add keys one2many, many2many
            if lines:
                data.update({list(lines[0])[0]: lines})

        # expresion python
        for exp in expressions:
            # Ref: base/models/ir_actions.py
            data.update({exp: safe_eval(exp, eval_context)})
        pprint.pprint(data, indent=2, width=128)
        return data

    def render_any_docs(self, res_ids=None, data=None):
        if not data:
            data = {}
        docids = res_ids

        report_obj = self.env[self.model]
        output_file = self.output_file
        docs = report_obj.browse(docids)
        report_name = self.name
        zip_filename = report_name
        if self.print_report_name and not len(docs) > 1:
            report_name = safe_eval(self.print_report_name, {'object': docs, 'time': time})
        if not self.template_id:
            raise ValidationError('Report file template not found.')

        in_stream = io.BytesIO(standard_b64decode(self.template_id.datas))
        # Render tmpl easy
        # in_stream = odoo.modules.get_module_resource('merge_docx', 'templates', "Practical-Business-Python.docx")
        if not in_stream:
            raise ValidationError('File template not found.')

        def close_streams(streams):
            for stream in streams:
                try:
                    stream.close()
                except Exception:
                    pass

        def merge_pdfs(streamsx):
            # Build the final pdf.
            writer = PdfFileWriter()
            for stream in streamsx:
                reader = PdfFileReader(stream)
                writer.appendPagesFromReader(reader)
            result_stream = io.BytesIO()
            streamsx.append(result_stream)
            writer.write(result_stream)
            result = result_stream.getvalue()
            # We have to close the streams after PdfFileWriter's call to write()
            close_streams(streamsx)
            return result

        def postprocess_report(report, record, buffer):
            if report.attachment:
                attachment_id = report.retrieve_attachment(record)
                if not attachment_id:
                    report.postprocess_pdf_report(record, buffer)

        if not docids:
            pass

        full_data = []
        full = False
        streams = []

        document = MailMerge(in_stream)
        # fields_template = {'o.partner_id.name.upper()', 'o.state', 'o.client_order_ref', 'o',
        #    'o.order_line.product_id.name', 'o.order_line.product_uom_qty', 'o.order_line.product_id.name.upper()', "o.order_line.bf_tax_id",
        #    "o.date_order", "o.validity_date", "o.expected_date.date()", "o.amount_total", "o.require_signature",
        #    "o.currency_rate", "o.amount_undiscounted", "o.date_order.date()",
        #    "o.partner_id.child_ids.name", "o.partner_id.child_ids.phone", "o.partner_id.category_id.name", "o.partner_id.category_id.active",
        #    "o.partner_id.bf_category_id.upper()", "o.partner_id.bf_label_phone.upper()", "user.name", "time", "env"}
        fields_template = document.get_merge_fields()
        print("fields_template", fields_template)
        # Gits private https://gist.github.com/dperaltab/1ef2452389e321248ec2faeef6ad1886
        lang = self.env.user.lang or 'en_US'
        for i, doc in enumerate(docs):
            if hasattr(doc, 'context_lang'):
                lang = doc.context_lang() or lang
            data = self.docx_values(doc.with_context(lang=lang), fields_template)
            if self.output_file == 'pdf':
                # Multi
                if i:
                    document = MailMerge(in_stream)
                    fields_template = document.get_merge_fields()
                temp = tempfile.NamedTemporaryFile()
                document.merge(**data)
                document.write(temp)
                document.close()
                temp.seek(0)
                out = compile_file(get_command('pdf', temp.name))
                content_stream = io.BytesIO(out)
                streams_record = [content_stream]

                if self.merge_pdf:
                    if hasattr(doc, 'list_pdf'):
                        if hasattr(doc, 'context_lang'):
                            lang = doc.context_lang() or lang
                        list_pdf = doc.with_context(lang=lang).list_pdf()
                        streams_record += list_pdf
                if self.merge_template_id:
                    if hasattr(doc, 'merge_report'):
                        if doc.merge_report:
                            pdf_content, ext = self.merge_template_id.render_qweb_pdf(doc.id)
                            streams_record.append(io.BytesIO(pdf_content))
                    else:
                        pdf_content, ext = self.merge_template_id.render_qweb_pdf(doc.id)
                        streams_record.append(io.BytesIO(pdf_content))
                result = merge_pdfs(streams_record)
                streams.append(io.BytesIO(result))
                postprocess_report(self, doc, io.BytesIO(result))
                temp.close()
                if len(docids) == 1:
                    return MIME_DICT['pdf'], result, report_name, 'pdf'
            else:
                full = True
                if self.attachment:
                    docx_temp = tempfile.NamedTemporaryFile()
                    document_attachment = MailMerge(in_stream)
                    document_attachment.merge(**data)
                    document_attachment.write(docx_temp)
                    document_attachment.close()
                    docx_temp.seek(0)
                    postprocess_report(self, doc, io.BytesIO(docx_temp.read()))
                    docx_temp.close()
                full_data.append(data)

        if streams:
            result = merge_pdfs(streams)
            return MIME_DICT['pdf'], result, zip_filename, 'pdf'
        if full:
            document.merge_templates(full_data, separator='page_break')
            temp_full = tempfile.NamedTemporaryFile()
            document.write(temp_full)
            document.close()
            temp_full.seek(0)
            if not output_file or output_file == 'docx':
                out = temp_full.read()
                temp_full.close()
                return MIME_DICT['docx'], out, report_name, 'docx'
            elif output_file == 'pdf':
                out = compile_file(get_command('pdf', temp_full.name))
                temp_full.close()
                return MIME_DICT[output_file], out, report_name, output_file
