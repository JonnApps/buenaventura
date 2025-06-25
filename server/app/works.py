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
except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


class Works() :
    db = None
    url_base : str = None
    headers = None
    aprdz_forder_id : str = None
    cmpnr_forder_id : str = None
    mstrs_forder_id : str = None
    works_mstrs : list = []
    works_cmpnr : list = []
    works_aprdz : list = []

# ==============================================================================
    def __init__(self) :
        try:
            host = str(os.environ.get('HOST_BD','192.168.0.15'))
            port = int(os.environ.get('PORT_BD', 3306))
            user_bd = str(os.environ.get('USER_BD','logia'))
            pass_bd = str(os.environ.get('PASS_BD','RL188#2022'))
            eschema = str(os.environ.get('SCHEMA_BD','gral-purpose'))

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
                    if doc.type == 'WORK' :
                        works.append(doc)
                    if doc.type == 'PROGRAM' :
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
    def get_other_docs(self, grade_qh: int ) :
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
    def get_all_docs(self, ) :
        works = []
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s order by w.date desc"""
                cursor.execute(sql, '3' )
                results = cursor.fetchall()
                for row in results:
                    doc = Work( row )
                    works.append(doc)
        except Exception as e:
            print("ERROR get_all_docs():", e)
        return works
# ==============================================================================
    def save(self, work ) :
        success = False
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                date : datetime = datetime.strptime(work.date_hm, "%d/%m/%Y %H:%M")
                small_photo = None
                if work.type == 'ADDITIONAL' :
                    small_photo = 'image/small_1.png'
                    if work.grade == 2 :
                        small_photo = 'image/small_2.png'
                    if work.grade == 3 :
                        small_photo = 'image/small_3.png'

                sql = """insert into works (namefile, title, author, grade, date, type, description, small_photo, md5sum) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, ( work.namefile, work.title, work.author, str(work.grade), date.strftime('%Y-%m-%d %H:%M:%S'), work.type, work.description, small_photo, work.md5sum ) )
                self.db.commit()
                success = True
        except Exception as e:
                print("ERROR save():", e)
        return success

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

# ==============================================================================
# Se obtiene el PDF del documento
# ==============================================================================
    def get_pdf_file(self, id_work : str, grade_doc : str = None, name_file : str = None ) :
        data_base64 = None 
        mime_type = None
        doc : Work = None
        # primero se obtiene el trabajo
        try :
            logging.info('Se obtienen la url del documento Id: ' + str(id_work) ) 
            if self.is_numeric(id_work) == True :
                if self.is_connect() :
                    cursor = self.db.cursor()
                    sql = """select * from works w where id = %s"""
                    cursor.execute(sql, str(id_work) )
                    results = cursor.fetchall()
                    for row in results: 
                        doc = Work( row )
                        logging.info('#### Documento encontrado en BD: ' + str(row) )
                    if doc != None :
                        data_json = {
                            'data' : {
                                'folder' : doc.namegrother,
                                'name_file' : doc.namefile,
                                'md5sum' : doc.md5sum
                            },
                            'type' : 'clear'
                        }
                        data_base64, mime_type = self.get_document(data_json)  
                else :
                    logging.error('No hay conexion a la BD')
            else :
                logging.info('Documento Id ' + str(id_work) + ' no encontrado en BD, lo busco en Drive')
                file = name_file.replace('drive-', '')
                folder = self.get_folders(grade_doc)[0]
                if self.get_drive_document('/tmp', file, folder) == True :
                    path_file = '/tmp/' + file
                    data_base64 = None
                    file_bytes = None
                    with open(path_file, "rb") as pdf_file:
                        file_bytes = base64.b64encode(pdf_file.read())
                    if file_bytes != None :
                        data_base64 = file_bytes.decode('utf-8')
                    mime_type = self.get_mime_type(file)
        except Exception as e:
            print("ERROR BD:", e)
        return data_base64, mime_type

    def is_numeric(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_document(self, data_json: str) :
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

    def get_drive_documents(self, grade : str) :
        documents : list = []
        try :
            logging.info('Solicita documentos de carpeta de ' + grade)
            
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
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json, 'type': 'clear'}), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200:
                data_response = resp.json()
                files_response = None
                try :
                    files_response = data_response['data']
                except Exception as e:
                    files_response = None
                if files_response != None and len(files_response) > 0 :
                    logging.info('Documentos encontrados en drive ' + str(len(files_response))) 
                    for doc in files_response :
                        documents.append( { 
                            'id' : doc['id'], 
                            'title' : str(self.clean_text(str(doc['title']), str(doc['fileExtension']))),
                            'mime_type' : doc['mimeType'],
                            'md5sum' : doc['md5Checksum'],
                            'size' : doc['fileSize'],
                            'author' : doc['lastModifyingUser']['displayName'],
                            'url' : doc['alternateLink'],
                            'small_photo' : doc['lastModifyingUser']['picture']['url'],
                            'namegrade': str(self.get_grade(str(grade))),
                            'created_at': doc['createdDate'],
                            'description': 'Documento de Drive',
                            'namefile': 'drive-' + str(doc['title']),
                            'grade': str(doc['grade_folder'])
                        })
        except Exception as e:
            print("ERROR get_drive_documents():", e)
        
        return documents

    def get_mime_type(self, file_name : str) :
        return mimetypes.guess_type(file_name)[0]

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

    def get_drive_document(self, path_to_save : str, name_file : str, folder : str = 'primero') :
        success = False
        try :
            logging.info('Solicita documento: ' + str(name_file) + ' en carpeta: ' + str(folder) ) 
            data_json = {
                'folder' : folder,
                'name_file' : name_file,
                'require_base64_file' : True,
                'require_detail' : False,
                'filters' : [
                    {
                        "filter_name": "mimeType",
                        "comparation": "=",
                        "filter_value": str(self.get_mime_type(name_file)),
                    },
                    #{
                    #    "filter_name": "name",
                    #    "comparation": "contains",
                    #    "filter_value": name_file,
                    #},
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
                    # data_response = base64.b64decode(data_file['file_b64'])
                    data_response = data_file['file_b64']
                    # os.makedirs(path_file, exist_ok=True)
                    file_path = os.path.join(path_to_save, str(name_file))
                    file = open(file_path, 'wb')
                    file_content = base64.b64decode((data_response) )
                    file.write(file_content)
                    file.close()
                    success = os.path.exists(str(file_path))
                    logging.info('Documento guardado en : ' + str(file_path))
                else :
                    logging.error('Respuesta NULA ' )
        except Exception as e:
            print("ERROR get_drive_document():", e)
            success = False
        
        return success
# ==============================================================================

class Work() :
    id = -1
    namefile = None
    title = None
    author = None
    grade = 0
    namegrade = None
    namegrother = None
    namegr = None
    date = None
    date_hm = None
    type = None
    description = None
    small_photo = None
    md5sum = None

    def __init__(self, row ) :
        self.id = int(row['id'])
        self.title = str(row['title'])
        self.author = str(row['author'])
        self.namefile = str(row['namefile'])
        self.grade = int(row['grade'])
        self.type = str(row['type'])
        self.description = str(row['description'])
        self.small_photo = str(row['small_photo'])
        self.md5sum = str(row['md5sum'])

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
        self.type = None
        self.date_hm = None
        self.namegr = None
        self.description = None
        self.small_photo = None
        self.md5sum = None
        self.namegrother = None