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

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Works() :
    db = None
    url_base : str = None
    headers = None
    notification_headers = None
    aprdz_forder_id : str = None
    cmpnr_forder_id : str = None
    mstrs_forder_id : str = None
    works_mstrs : list = []
    works_cmpnr : list = []
    works_aprdz : list = []

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
                
            api_key = str(os.environ.get('DOCS_API_KEY','None'))
            self.url_base = str(os.environ.get('API_BASE_URL','None'))
            authorization = str(os.environ.get('DOCS_API_AUTHORIZATION','None'))
            self.headers = {
                'Content-Type': 'application/json', 
                'Accept': 'application/json',
                'X-Api-Key': str(api_key), 
                'Authorization': str(authorization)
            }

            notification_api_key = str(os.environ.get('NOTIFICATION_API_KEY','None'))

            self.notification_headers = {
                'Content-Type': 'application/json', 
                'Accept': 'application/json',
                'x-api-key': str(notification_api_key)
            }

            self.aprdz_forder_id = str(os.environ.get('APRDZ_FORDER_ID','None'))
            self.cmpnr_forder_id = str(os.environ.get('CMPNR_FORDER_ID','None'))
            self.mstrs_forder_id = str(os.environ.get('MSTRS_FORDER_ID','None'))
        except Exception as e :
            print("ERROR Contructor Works() :", e)
# ==============================================================================
    def __del__(self):
        if self.db != None:
            self.db.close()

# ==============================================================================
    def is_connect(self) :
        return self.db != None
    
    # ==============================================================================
    # obtiene los trabajos que se han registrado en la base de datos como los que vienen
    # y los que son presentes esta semana
    # ==============================================================================
    def get_works(self, grade_qh : int ) :
        works = []
        plans = []
        aux = []
        try :
            logging.info('Se obtienen los trabajos del grado: ' + str(grade_qh) ) 
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s and type in( 'WORK','PROGRAM' ) order by w.date desc"""
                cursor.execute(sql, str(grade_qh) )
                results = cursor.fetchall()
                for row in results:
                    doc = Work( row )
                    if doc.type_work == 'WORK' :
                        works.append(doc)
                    if doc.type_work == 'PROGRAM' :
                        aux.append(doc)
            else :
                logging.error('No hay conexion a la BD')
        except Exception as e:
            print("ERROR BD:", e)
        if aux != None and len(aux) :
            length = len(aux)
            for i in range(0, length ):
                plans.append(aux.pop()) 
        return works, plans
    # ==============================================================================
    # obtiene los trabajos que se han registrado en la base de datos como material 
    # adicional pero tambien los que se han subido a drive compartido
    # ==============================================================================
    def get_additional_works(self, grade_qh: int ) :
        works = []
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s and type = 'ADDITIONAL' order by w.date desc"""
                cursor.execute(sql, str(grade_qh) )
                results = cursor.fetchall()
                for row in results:
                    doc = Work( row )
                    works.append(doc)
        except Exception as e:
            print("ERROR BD:", e)
        return works
    # ==============================================================================
    # obtiene todos trabajos que se han registrado en la base de datos 
    # ==============================================================================
    def get_all_docs(self, grade_qh: str = '3') :
        works = []
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s order by w.date desc"""
                cursor.execute(sql, grade_qh )
                results = cursor.fetchall()
                for row in results:
                    doc = Work( row )
                    works.append(doc)
        except Exception as e:
            print("ERROR get_all_docs():", e)
        return works
    # ==============================================================================
    # Actualiza o guarda el trabajo en la base de datos
    # ==============================================================================
    def save(self, work ) :
        saved : Work = None
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                date : datetime = datetime.strptime(work.date_hm, "%d/%m/%Y %H:%M")
                small_photo = None
                if work.type_work == 'ADDITIONAL' :
                    small_photo = 'image/small_1.png'
                    if work.grade == 2 :
                        small_photo = 'image/small_2.png'
                    if work.grade == 3 :
                        small_photo = 'image/small_3.png'
                # guarda o actualiza
                if int(work.id) >= 0 :
                    sql = """select * from works where id = %s"""
                    cursor.execute(sql, ( str( work.id ), ) )
                    results = cursor.fetchall()
                    if len(results) == 1 :
                        logging.info('Actualizando el trabajo: ' + work.namefile )
                        sql = """update works set namefile = %s, title = %s, author = %s, grade = %s, date = %s, type = %s, description = %s, small_photo = %s, md5sum = %s, source = %s where id = %s"""
                        cursor.execute(sql, ( work.namefile, work.title, work.author, str(work.grade), date.strftime('%Y-%m-%d %H:%M:%S'), work.type_work, work.description, small_photo, work.md5sum, work.source, str(work.id) ) )
                        self.db.commit()
                        success = True
                else:
                    logging.info('Insertando el trabajo: ' + work.namefile )
                    sql = """insert into works (namefile, title, author, grade, date, type, description, small_photo, md5sum, source) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql, ( work.namefile, work.title, work.author, str(work.grade), date.strftime('%Y-%m-%d %H:%M:%S'), work.type_work, work.description, small_photo, work.md5sum, work.source ) )
                    self.db.commit()
                saved = self.search(work.md5sum, work.source)  
        except Exception as e:
                print("ERROR save():", e)
        return saved

    def search(self, md5sum: str, source: str) :
        work = None
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works where md5sum = %s and source = %s"""
                cursor.execute(sql, ( md5sum, source ) )
                results = cursor.fetchall()
                if len(results) == 1 :
                    work = Work( results[0] )
        except Exception as e:
                print("ERROR search():", e)
        return work

    def search_for_id(self, id_file: str) :
        work = None
        try :
            logging.info('Busca documento en la base de datos por Id: ' + id_file ) 
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works where id = %s"""
                cursor.execute(sql, ( id_file ) )
                results = cursor.fetchall()
                if len(results) == 1 :
                    work = Work( results[0] )
        except Exception as e:
                print("ERROR search_for_id():", e)
        return work

    def delete(self, id_file: int) :
        success = False
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """delete from works where id = %s"""
                cursor.execute(sql, ( str(id_file), ) )
                self.db.commit()
                success = True
        except Exception as e:
                print("ERROR delete():", e)
        return success

    def upload(self, request) :
        data_response = { 'md5': None, 'message': 'Servicio ejecutado exitosamente', 'size': 0 }
        http_code : int = 201
        m1 = time.monotonic()
        file_path : str = None
        try :
            request_data = request.get_json()
            # payload para api de documentos
            json_data = {
                'type':  'clear',
                'data': {
                    'name':  str(request_data['file_name']),
                    'type': str(request_data['file_type']),
                    'fileb64': str(request_data['file_data']),
                    'folder': str(request_data['file_folder']),
                }
            }
            logging.info('Solicita subir archivo ' + str(request_data['file_name']) + ' en /' + str(request_data['file_folder']) )
            resp = None
            url = self.url_base + '/docs/s3/upload'
            logging.info('URL Post: ' + url )
            resp = requests.post(url, data = json.dumps(json_data), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            http_code = resp.status_code
            if http_code == 201 :
                response = resp.json()
                logging.info('Response ' + str( response )  )
                data_file = None
                try :
                    data_file = response['data']
                except Exception as e:
                    data_file = None
                
                if data_file != None :
                    logging.info('Documento de ' + str(data_file['size_bytes']) + ' bytes subido') 

                    data_response['md5'] = str(data_file['md5'])
                    data_response['size'] = int(str(data_file['size_bytes']))
                    data_response['message'] = 'Documento subido exitosamente'
                else :
                    logging.error('Respuesta API NULA' )
        except Exception as e:
            logging.error('Error: ' + str(e) )
            http_code = 403
            data_response = { 'md5': None, 'size': 0, 'message': 'Error: ' + str(e) }

        logging.info("Servicio Ejecutado en " + str(time.monotonic() - m1) + " sec." )
        return data_response, http_code 

    def load_drive_docs(self, grade : str ):
        name_thread = '[' + threading.current_thread().name + '-' + str(threading.get_native_id()) + '] '
        try :
            logging.info(name_thread + 'Solicita documentos de carpeta de ' + grade)
            data_json = {
                'folders' : self.get_folders(grade),
                'filters' : [
                    {
                        "filter_name": "mimeType",
                        "comparation": "=",
                        "filter_value": "application/pdf",
                    }
                ],
            }
            resp = None
            url = self.url_base + '/docs/drive/list'
            m1 = time.monotonic()
            logging.info(name_thread + 'URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json, 'type': 'clear'}), headers = self.headers, timeout = 15)
            logging.info(name_thread + 'Response[' + str(resp.status_code) + '] ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200:
                data_response = resp.json()
                files_response = None
                try :
                    files_response = data_response['data']
                except Exception as e:
                    files_response = None
                if files_response != None and len(files_response) > 0 :
                    logging.info(name_thread + 'Documentos encontrados en drive ' + str(len(files_response))) 
                    for doc in files_response :
                        work = self.search( str(doc['md5Checksum']), 'DRIVE' )
                        if work == None :
                            logging.info(name_thread + 'Se guarda en BD documento ' + str(doc['title'])) 
                            date : datetime = datetime.strptime(str(doc['createdDate']), '%Y-%m-%dT%H:%M:%S.%f%z')
                            document = Work( {
                                'id' : '-1', 
                                'title' : str(self.clean_text(str(doc['title']), str(doc['fileExtension']))),
                                'author' : 'QH:.' + str(doc['lastModifyingUser']['displayName']),
                                'namefile': str(doc['title']),
                                'grade': str(doc['grade_folder']),
                                'type' : 'ADDITIONAL',
                                'description': 'Documento de Drive',
                                'md5sum' : doc['md5Checksum'],
                                'source': 'DRIVE',
                                'small_photo': 'image/small_1.png',
                                'url' : str(doc['alternateLink']),
                                'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                            } )
                            if self.save(document) != None :
                                logging.info(name_thread + 'Documento guardado, se notifica ' )
                                self.notify( str(document.title), str(document.grade), str(document.date) )
        except Exception as e:
            print(name_thread + "ERROR load_drive_docs():", e)

    def notify(self, title : str, grade : str, date : str ) :
        try :
            grade_str : str = str(grade).lower().strip()
            logging.info('Notificando documento de ' + str(grade_str))

            body : str = 'El trabajo titulado: ' + str(title) + ' a quedado disponible con fecha: ' + str(date) + '\nPara descargarlo visita https://logia.buenaventuracadiz.cl' 

            subject : str = '[Aviso] Nuevo documento de '
            mail : str = 'aprendices188@googlegroups.com'

            if grade_str.find('1') > -1 :
                mail = 'aprendices188@googlegroups.com'
                subject += 'aprendiz'
            elif grade_str.find('2') > -1 :
                mail = 'companeros188@googlegroups.com'
                subject += 'compañero'
            elif grade_str.find('3') > -1 :
                mail = 'maestros188@googlegroups.com'
                subject += 'maestro'
            else :
                logging.info('Se envia a jonnattan solo !!!')
                mail = 'jonnattan@gmail.com'

            subject += ' disponible'

            data = {
                'to' : mail,
                'subject' : subject,
                'body' : body
            }
            resp = None
            url: str = self.url_base + '/notification/mail'
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({"type": "clear", "data": data}), headers = self.notification_headers, timeout = 15)
            if resp.status_code == 200:
                logging.info('Notificacion enviada')
            else :
                logging.error('Notificacion no enviada')
        except Exception as e:
            print("ERROR notify():", e)

    def process_drive_document(self, grade: str ) :
        self.th = threading.Thread(target=self.load_drive_docs, args=( grade ), name='th', daemon=True)
        self.th.start()
# ==============================================================================
# Se obtiene el PDF del documento
# ==============================================================================
    def get_pdf_file(self, id_work : str, grade_doc : str = None, name_file : str = None ) :
        data_base64 = None 
        mime_type = None
        doc : Work = None
        # primero se obtiene el trabajo
        try :
            doc = self.search_for_id(id_work)
            # si existe localmente se entrega el PDF al toke
            if doc != None :
                data_base64 = self.file_exists(doc.md5sum + self.get_extension(doc.namefile))
                if data_base64 != None : 
                    logging.info('Documento encontrado localmente, se entrega el PDF al toke')
                    mime_type = self.get_mime_type(doc.namefile)
                    return data_base64, mime_type
            # si no existe localmente primero se busca en S3
            if doc != None and doc.source == 'S3' :
                logging.info('Documento \"' + doc.namefile + '\" es de S3')
                data_json = {
                    'data' : {
                        'folder' : doc.namegrother,
                        'name_file' : doc.namefile,
                        'md5sum' : doc.md5sum
                    },
                    'type' : 'clear'
                }
                data_base64, mime_type = self.get_s3_document(data_json)  
            elif doc != None and doc.source == 'DRIVE' :
                logging.info('Documento \"' + doc.namefile + '\" es de Drive')
                folder = self.get_folders(grade_doc)[0]
                if self.get_drive_document('/tmp', doc, folder) == True :
                    path_file = doc.md5sum + self.get_extension(doc.namefile)
                    data_base64 = self.file_exists(path_file)
                    mime_type = self.get_mime_type(doc.namefile)
            else :
                logging.error('Documento ' + id_work + ' no encontrado')
        except Exception as e:
            print("ERROR get_pdf_file():", e)
        return data_base64, mime_type

    def get_s3_document(self, data_json: str) :
        data_response = None
        mime_type = None
        try :
            logging.info('Solicita Buscar Documento ID: ' + str(data_json)) 
            resp = None
            url = self.url_base + '/docs/s3/read'
            m1 = time.monotonic()
            logging.info('URL Post: ' + url )
            resp = requests.post(url, data = json.dumps(data_json), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200 :
                data_response = resp.json()
                data_file = None
                try :
                    data_file = data_response['data']
                except Exception as e:
                    data_file = None
                if data_file != None :
                    logging.info('Documento encontrado de ' + str(data_file['size_bytes']) + ' bytes' + ' type: ' + str(data_file['type']) ) 
                    # data_response = base64.b64decode(data_file['file_b64'])
                    data_response = data_file['file_b64']
                    mime_type = data_file['type']
                    # se guarda el documento localmente para ser m'as rapido la carga
                    self.save_doc_file( data_file['md5'] + self.get_extension(data_json['data']['name_file']), data_response )
                else :
                    logging.error('Respuesta NULA ' )
        except Exception as e:
            print("ERROR get_document():", e)
        
        return data_response, mime_type
            
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
        return mimetypes.guess_type(file_name)[0]

    def get_extension(self, file_name : str) :
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

        # ==============================================================================
    # limpia texto y normaliza sus letras
    # ==============================================================================
    def clean_text( self, texto: str, ext: str ) :
        text = texto.replace('_', ' ')
        text = text.replace('.', '')
        text = text.replace(ext, '')
        return text 

    def get_drive_document(self, path_to_save : str, doc, folder : str = 'primero') :
        success = False
        try :
            name_file : str = doc.namefile
            logging.info('Solicita documento ' + str(name_file) + ' en la carpeta /' + str(folder) ) 
            data_json = {
                'folder' : folder,
                'name_file' : name_file,
                'md5sum' : doc.md5sum,
                'require_base64_file' : True,
                'require_detail' : False,
                'filters' : [
                    {
                        "filter_name": "mimeType",
                        "comparation": "=",
                        "filter_value": str(self.get_mime_type(name_file)),
                    },
                    {
                        "filter_name": "title",
                        "comparation": "=",
                        "filter_value": name_file,
                    }
                ],
            }
            resp = None
            url : str = self.url_base + '/docs/drive/read'
            m1 = time.monotonic()
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json, 'type': 'clear'}), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200 :
                data_response = resp.json()
                data_file = None
                try :
                    data_file = data_response['data']
                except Exception as e:
                    data_file = None
                if data_file != None :
                    logging.info('Documento encontrado de ' + str(data_file['size_bytes']) + ' bytes' + ' type: ' + str(data_file['type']) ) 
                    data_response = data_file['file_b64']
                    if str(data_file['type']).lower().strip().find('application/pdf') >= 0 :
                        success = self.save_doc_file( data_file['md5']+self.get_extension(data_file['title']), data_response )
                    else :
                        logging.info('Guarda ' + name_file + ' en: ' + path_to_save )
                        file_path = os.path.join('/tmp', str(name_file))
                        file = open(file_path, '+wb')
                        file_content = base64.b64decode((data_response) )
                        file.write(file_content)
                        file.close()
                        success = os.path.exists(str(file_path))
                        try:
                            uid = pwd.getpwnam('logia').pw_uid
                            gid = grp.getgrnam('logia').gr_gid
                            os.chown(file_path, uid, gid)
                            # os.chown(file_path, 1100, 1101)
                            shutil.move(file_path, path_to_save)
                        except FileNotFoundError:
                            logging.error(f"Error: El archivo '{file_path}' no fue encontrado.")
                            success = False
                        except Exception as e:
                            logging.error(f"Ocurrió un error al mover el archivo: {e}")
                            success = False

                        logging.info('Documento guardado en : ' + str(file_path))
                else :
                    logging.error('Respuesta NULA ' )
            else :
                logging.error('Respuesta [' + str(resp.status_code) + '] ' + str(resp) )
        except Exception as e:
            print("ERROR get_drive_document():", e)
            success = False
        return success

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

class Work() :
    id = -1
    namefile : str = None
    title : str = None
    author : str = None
    grade = 0
    namegrade : str = None
    namegrother : str = None
    namegr : str = None
    date : str = None
    date_hm : str = None
    type_work : str = None
    description : str = None
    small_photo : str = None
    md5sum : str = None
    source : str = None
    url : str = None

    def __init__(self, row ) :
        self.id = int(row['id'])
        self.title = str(row['title'])
        self.author = str(row['author'])
        self.namefile = str(row['namefile'])
        self.grade = int(row['grade'])
        self.type_work = str(row['type'])
        self.description = str(row['description'])
        self.small_photo = str(row['small_photo'])
        self.md5sum = str(row['md5sum'])
        self.source = str(row['source'])
        self.url = str(row['url'])
        
        if self.grade == 1 :
            self.namegrade = 'Aprendiz'
            self.namegr = 'Primer Grado'
            self.namegrother = 'primero'
        elif self.grade == 2 :
            self.namegrade = 'Compañero'
            self.namegr = 'Segundo Grado'
            self.namegrother = 'segundo'
        elif self.grade == 3 :
            self.namegrade = 'Maestro'
            self.namegr = 'Tercer Grado'
            self.namegrother = 'tercero'
        else :
            self.namegrade = 'Un dios'
            self.namegr = '33 avo Grado'

        aux = str(row['date'])
        my_date = datetime.strptime(aux, '%Y-%m-%d %H:%M:%S')
        self.date = my_date.strftime('%d/%m/%Y')
        self.date_hm = my_date.strftime('%d/%m/%Y %H:%M')

    def __del__(self):
        self.namefile = None
        self.title = None
        self.author = None
        self.grade = 0
        self.id = -1
        self.date = None
        self.namegrade = None
        self.type_work = None
        self.date_hm = None
        self.namegr = None
        self.description = None
        self.small_photo = None
        self.md5sum = None
        self.namegrother = None
        self.source = None
        self.url = None