# -*- coding: utf-8 -*-
import logging
import base64
import datetime
import xlrd
from sys import platform
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class FuelTool(models.Model):
    _name = 'fuel.tool'

    file = fields.Binary(string='File')
    block_result = fields.Text(string='Resultado')
    report = fields.Many2many('fuel.tool.report', string='Reporte')

    def generate_xml(self):

        view_ref = self.env['ir.model.data'].get_object_reference('fuel_tool', 'fuel_tool_xml_form')
        view_id = view_ref[1] if view_ref else False

        self.create_xml()

        return {
            'name': 'XML',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fuel.tool.xml',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def import_xlm(self):
        excel = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
        # excel = xlrd.open_workbook('C:\Users\Jesus Rojas\Desktop\Experimento.xlsx')
        _sheet = []
        for sheet in excel.sheets():
            for row in range(sheet.nrows):
                row_list = []
                for col in range(sheet.ncols):
                    value = sheet.cell(row, col).value
                    if sheet.cell(row, col).ctype == 3 and col == 1:
                        xls_date = xlrd.xldate_as_tuple(value, excel.datemode)
                        year, month, day, hour, minute, second = xls_date
                        real_date = datetime.date(year, month, day).strftime('%y-%m-%d')
                        value = real_date

                    elif sheet.cell(row, col).ctype == 3 and col == 2:
                        if value > 0 and value < 1:
                            xls_date = xlrd.xldate_as_tuple(value, excel.datemode)
                            year, month, day, hour, minute, second = xls_date
                            real_date = datetime.time(hour, minute, second).strftime('%H:%M:%S')
                            value = real_date
                        else:
                            xls_date = xlrd.xldate_as_tuple(0.0, excel.datemode)
                            year, month, day, hour, minute, second = xls_date
                            real_date = datetime.time(hour, minute, second).strftime('%H:%M:%S')
                            value = real_date
                    row_list.append(value)
                _sheet.append(row_list)

        self.update_report(_sheet)
        self.block_result = _sheet

    def update_report(self, sheet):

        sql = 'delete from fuel_tool_report'
        self.env.cr.execute(sql)

        fuel_report = self.env['fuel.tool.report']
        sql_root = "insert into fuel_tool_report("
        sql_mid = ") values("
        for line in sheet:
            i = 0
            _logger.info(line)
            for item in line:
                _logger.info(item)
                if i == 0:
                    sql_root = sql_root + "asset"
                    sql_mid = sql_mid + "'" + str(item) + "'"
                elif i == 1:
                    sql_root = sql_root + ",date"
                    sql_mid = sql_mid + ",'" + str(item) + "'"
                elif i == 2:
                    sql_root = sql_root + ",hour"
                    sql_mid = sql_mid + ",'" + str(item) + "'"
                elif i == 3:
                    sql_root = sql_root + ",gallons"
                    sql_mid = sql_mid + ",'" + str(item) + "'"
                else:
                    sql_root = sql_root + ",custom_field" + str(i)
                    sql_mid = sql_mid + ",'" + str(item) + "'"
                i += 1
            sql = sql_root + sql_mid + ")"
            _logger.info(sql)
            self.env.cr.execute(sql)
            sql_root = "insert into fuel_tool_report("
            sql_mid = ") values("
            # break
        self.report = fuel_report.search([])

    def create_xml(self):


        # HEADER
        header_report = self.env['fuel.tool.report'].search([], limit=1)
        for record in header_report:
            sql = "select * from fuel_tool_report where id = %s" % record.id
            self.env.cr.execute(sql)
            _header = self.env.cr.dictfetchall()
            _header = dict((k, v) for k, v in _header[0].iteritems() if v)

        for k in _header:
            if k not in ('asset', 'date', 'hour', 'gallons', 'id'):
                _header[k] = "\t\t\t\t\t<CustomFieldName>" + _header[k] + "</CustomFieldName>\n"

        # VALUES
        i = False
        fuel_report = self.env['fuel.tool.report'].search([])
        template = '<?xml version="1.0" encoding="utf-8"?>\n'
        template += '<Fuel fileid="'+str(datetime.datetime.now())+'">\n'
        template += '\t<Refills>\n'
        for record in fuel_report:
            if i:
                sql = "select * from fuel_tool_report where id = %s" % record.id
                self.env.cr.execute(sql)
                _values = self.env.cr.dictfetchall()
                _values = dict((k, v) for k, v in _values[0].iteritems() if v)
                for k in _values:
                    if k == 'asset':
                        vehicleid_template = '\t\t\t<VehicleID>'+_values[k]+'</VehicleID>\n'
                    if k == 'date':
                        timestamp_date = '\t\t\t<TimeStamp>'+_values[k]+'T'
                    if k == 'hour':
                        timestamp_hour = _values[k]+'</TimeStamp>\n'
                    if k == 'gallons':
                        volume_template = '\t\t\t<Volume>'+str(_values[k])+'</Volume>\n'
                header_template = vehicleid_template+(timestamp_date+timestamp_hour)+volume_template

                template += '\t\t<Refill>\n'
                template += header_template
                template += '\t\t\t<CustomFields>\n'
                for k in _values:
                    if k not in ('asset', 'date', 'hour', 'gallons', 'id'):
                        template += '\t\t\t\t<CustomField>\n'
                        template += str(_header[k])
                        if _values[k] == 'n/a':
                            result = ''
                        else:
                            result = _values[k]
                        template += '\t\t\t\t\t<CustomFieldValue>'+str(result)+'</CustomFieldValue>\n'
                        template += '\t\t\t\t</CustomField>\n'
                template += '\t\t\t</CustomFields>\n'
                template += '\t\t</Refill>\n'
            else:
                i = True
        template += '\t</Refills>\n'
        template += '</Fuel>'

        _logger.info(template)
        sql = 'delete from fuel_tool_xml'
        self.env.cr.execute(sql)
        sql = "insert into fuel_tool_xml (report) values ('%s')" % template
        self.env.cr.execute(sql)


class FuelToolSheet(models.TransientModel):
    _name = 'fuel.tool.xml'

    def _default_report(self):

        return self.env['fuel.tool.xml'].search([]).report

    report = fields.Text(string='Reporte', default=_default_report)
    binary_xml = fields.Binary(string='Descargar XML')
    binary_string = fields.Char('Descargar XML')

    @api.onchange('report')
    def download_xml(self):
        xml_read = False
        if platform == 'win32':
            xml_write = open('C:\Users\openpgsvc\comp_file.xml', 'w')
            xml_write.write(self.report)
            xml_write.close()
            xml_read = open('C:\Users\openpgsvc\comp_file.xml', 'r')
        elif platform == 'linux2':
            xml_write = open('/home/administrator/comp_file.xml', 'w')
            xml_write.write(self.report)
            xml_write.close()
            xml_read = open('/home/administrator/comp_file.xml', 'r')

        self.write({
            'binary_string': 'fuel_file'+str(datetime.datetime.now().strftime('%d%m%y%H%M%S'))+'.xml',
            'binary_xml': base64.encodestring(xml_read.read())
        })
        return {'type': 'ir.action.do_nothing'}


class FuelToolReport(models.Model):
    _name = 'fuel.tool.report'

    asset = fields.Char(string='Ficha')
    date = fields.Char(string='Día, Mes y Año')
    hour = fields.Char(string='Hora')
    gallons = fields.Char(string='Galones')

    custom_field4 = fields.Char(string='.')
    custom_field5 = fields.Char(string='.')
    custom_field6 = fields.Char(string='.')
    custom_field7 = fields.Char(string='.')
    custom_field8 = fields.Char(string='.')
    custom_field9 = fields.Char(string='.')
    custom_field10 = fields.Char(string='.')
    custom_field11 = fields.Char(string='.')
    custom_field12 = fields.Char(string='.')
    custom_field13 = fields.Char(string='.')
    custom_field14 = fields.Char(string='.')
    custom_field15 = fields.Char(string='.')
    custom_field16 = fields.Char(string='.')
    custom_field17 = fields.Char(string='.')
    custom_field18 = fields.Char(string='.')
    custom_field19 = fields.Char(string='.')
    custom_field20 = fields.Char(string='.')
    custom_field21 = fields.Char(string='.')
    custom_field22 = fields.Char(string='.')
    custom_field23 = fields.Char(string='.')
    custom_field24 = fields.Char(string='.')
    custom_field25 = fields.Char(string='.')
    custom_field26 = fields.Char(string='.')
    custom_field27 = fields.Char(string='.')
    custom_field28 = fields.Char(string='.')
    custom_field29 = fields.Char(string='.')
    custom_field30 = fields.Char(string='.')
    custom_field31 = fields.Char(string='.')
    custom_field32 = fields.Char(string='.')
    custom_field33 = fields.Char(string='.')
    custom_field34 = fields.Char(string='.')
    custom_field35 = fields.Char(string='.')
    custom_field36 = fields.Char(string='.')
    custom_field37 = fields.Char(string='.')
    custom_field38 = fields.Char(string='.')
    custom_field39 = fields.Char(string='.')
    custom_field40 = fields.Char(string='.')
    custom_field41 = fields.Char(string='.')
    custom_field42 = fields.Char(string='.')
    custom_field43 = fields.Char(string='.')
    custom_field44 = fields.Char(string='.')
    custom_field45 = fields.Char(string='.')
    custom_field46 = fields.Char(string='.')
    custom_field47 = fields.Char(string='.')
    custom_field48 = fields.Char(string='.')
    custom_field49 = fields.Char(string='.')
    custom_field50 = fields.Char(string='.')
