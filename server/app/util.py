try:
    import logging
    import sys
    import os
    import time
    import json
    import requests
    import mimetypes
    import pymysql.cursors
    from datetime import datetime, timedelta
    from flask import Flask, render_template, abort, make_response, request, redirect, jsonify, send_from_directory
    import base64
    import threading
    import shutil
    import pwd
    import grp
    from work import Work


except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Util() :
    db = None
    url_base : str = None
    notification_headers = None
    aprdz_forder_id : str = None
    cmpnr_forder_id : str = None
    mstrs_forder_id : str = None
    mail_aprendices : str = None
    mail_companeros : str = None
    mail_maestros : str = None

    # ==============================================================================
    def __init__(self) :
        try:
            host = str(os.environ.get('HOST_BD','dev.jonnattan.com'))
            port = int(os.environ.get('PORT_BD', 3306))
            user_bd = str(os.environ.get('USER_BD','----'))
            pass_bd = str(os.environ.get('PASS_BD','*****'))
            eschema = str(os.environ.get('SCHEMA_BD','*****'))

            self.db = pymysql.connect(host=host, port=port, 
                user=user_bd, password=pass_bd, database=eschema, 
                cursorclass=pymysql.cursors.DictCursor)
                
            self.url_base = str(os.environ.get('API_BASE_URL','None'))

            self.notification_headers = {
                'Content-Type': 'application/json', 
                'Accept': 'application/json',
                'x-api-key': str( os.environ.get('NOTIFICATION_API_KEY','None'))
            }

            self.aprdz_forder_id = str(os.environ.get('APRDZ_FORDER_ID','None'))
            self.cmpnr_forder_id = str(os.environ.get('CMPNR_FORDER_ID','None'))
            self.mstrs_forder_id = str(os.environ.get('MSTRS_FORDER_ID','None'))

            self.mail_aprendices = str(os.environ.get('MAIL_APRENDICES','None'))
            self.mail_companeros = str(os.environ.get('MAIL_COMPANEROS','None'))
            self.mail_maestros = str(os.environ.get('MAIL_MAESTROS','None'))

        except Exception as e :
            print("ERROR Contructor Util() :", e)
            
    # ==============================================================================
    def notify(self, work : Work, path : str = 'mail') :
        try :
            date_utc = datetime.now()
            str_date : str = datetime.strftime(date_utc, '%d/%m/%Y')
            date_work : datetime = datetime.strptime(work.date_hm, '%d/%m/%Y %H:%M')
            str_temp : str = ' que ha sido'
            if date_work > date_utc :
                str_temp = ' que será'
            str_tipo : str = 'material adicional'
            if work.type_work == 'PROGRAM' or work.type_work == 'WORK' :
                str_tipo = 'trabajo'

            grade_str : str = str(work.grade).lower().strip()

            body : str = 'QQHH:.\nEl ' + str_tipo + ' titulado \"' + str(work.title) + '\" de ' + str(work.namegr)
            
            if str_tipo == 'trabajo' :
                body += ', realizado por el ' + str(work.author) + ' y ' + str_temp
                body += ' presentado el día ' + str(work.date) 
            
            body += ' desde hoy se encuentra disponible para su visualización y/o descarga en el intranet.'
            body += '\nPor favor visita https://logia.buenaventuracadiz.cl para más información.' 
            body += '\n\nUn TAF'

            subject : str = '[Aviso] Nuevo Documento de ' + str(work.namegrade) + ' Disponible'
            mail : str = self.mail_aprendices

            if grade_str.find('1') > -1 :
                mail = self.mail_aprendices
            elif grade_str.find('2') > -1 :
                mail = self.mail_companeros
            elif grade_str.find('3') > -1 :
                mail = self.mail_maestros
            else :
                logging.info('Se envia a jonnattan solo !!!')
                mail = self.mail_aprendices

            logging.info('Notificando:  ' + str(subject))

            data = {
                'to' : mail,
                'subject' : subject,
                'body' : body
            }
            resp = None
            url: str = self.url_base + '/notification/' + path
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({"type": "clear", "data": data}), headers = self.notification_headers, timeout = 15)
            if resp.status_code == 200:
                logging.info('Notificacion enviada')
            else :
                logging.error('Notificacion no enviada')
        except Exception as e:
            print("ERROR notify():", e)


    def get_folders(self, grade : str) :
        folders : list = []
        int_grade : int = int(grade)
        if int_grade == 3 :
            folders.append('tercero')
            folders.append('segundo')
            folders.append('primero')
        elif int_grade == 2 :
            folders.append('segundo')
            folders.append('primero')
        elif int_grade == 1 :
            folders.append('primero')
        else :
            folders = []
        return folders


    def get_mime_type(self, file_name : str) :
        if file_name == None :
            return ''
        if file_name == '' :
            return ''
        return mimetypes.guess_type(file_name)[0]

    def get_extension(self, file_name : str) :
        if file_name == None :
            return ''
        if file_name == '' :
            return ''
        mimetype_str = mimetypes.guess_type(file_name)[0]
        return mimetypes.guess_extension(mimetype_str)

    def get_grade(self, grade : str) :
        if grade == '1' :
            return 'Aprendiz'
        elif grade == '2' :
            return 'Compañero'
        elif grade == '3' :
            return 'Maestro'
        else :
            return 'Un dios'

    def get_name(self, grade: int) :
        if grade == 1 :
            return 'Primer Grado'
        elif grade == 2 :
            return 'Segundo Grado'
        elif grade == 3 :
            return 'Tercer Grado'
        else :
            return None
    
    # ==============================================================================
    # limpia texto y normaliza sus letras
    # ==============================================================================
    def clean_text( self, texto: str, ext: str ) :
        text = texto.replace('_', ' ')
        text = text.replace('.', '')
        text = text.replace(ext, '')
        return text 

    def save_doc_file(self, name_file : str, data_base64) :
        success = False
        try :
            final_file : str = ROOT_DIR + '/static/docs/' + name_file
            logging.info('Guarda \"' + name_file + '\" en ruta: ' + final_file )
            file_path = os.path.join('/tmp', name_file )
            file = open(file_path, '+wb')
            file_content = base64.b64decode((data_base64) )
            file.write(file_content)
            file.close()
            uid = pwd.getpwnam('logia').pw_uid
            gid = grp.getgrnam('logia').gr_gid
            os.chown(file_path, uid, gid)
            shutil.move(file_path, final_file )
            success = os.path.exists( final_file )
        except FileNotFoundError:
            logging.error(f"Error: El archivo '{file_path}' no fue encontrado.")
            success = False
        except Exception as e:
            logging.error(f"Ocurrió un error al mover el archivo: {e}")
            success = False
        except Exception as e:
            print("ERROR save_doc_file():", e)
        logging.info('Documento guardado con exito... ' )
        return success

    def file_exists(self, full_file_path : str ) :
        data_base64 = None
        values: list = full_file_path.split('/')
        name_file : str = None
        if len(values) > 1 :
            name_file = values[len(values) - 1]
        else :
            name_file = full_file_path
        # lo busco localmente
        name_file = 'static/docs/' + name_file
        file_path: str = os.path.join(ROOT_DIR,  name_file )
        logging.info("Verifica si existe archivo: " + str( file_path ) )
        if os.path.exists(file_path) :
            file_bytes = None
            with open(file_path, "rb") as pdf_file:
                file_bytes = base64.b64encode(pdf_file.read())
                if file_bytes != None :
                    data_base64 = file_bytes.decode('utf-8')
            logging.info("Archivo encontrado!! " )
        return data_base64
# ==============================================================================
