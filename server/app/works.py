try:
    import logging
    import sys
    import os
    import time
    import json
    import requests
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
    url_base = 'https://dev.jonnattan.com/docs'
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
    
    def find_forders_ids(self) :

        # Si ya los tenemos no se hace nada
        if self.aprdz_forder_id != None and self.cmpnr_forder_id != None and self.mstrs_forder_id != None and self.works_mstrs != None and self.works_cmpnr != None and self.works_aprdz != None :
            return

        base_folder_id = str(os.environ.get('DRIVER_FOLDER_ID','None'))
        try :
            logging.info('Obtiene los Ids de las carpetas: ') 
            data_json = {
                'folder_id' : str(base_folder_id),
                'filters' : [
                    {
                        "filter_name": "mimeType",
                        "comparation": "=",
                        "filter_value": "application/vnd.google-apps.folder",
                    }
                ],
            }
            resp = None
            url = self.url_base + '/drive/list'
            m1 = time.monotonic()
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json}), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200 :
                data_response = resp.json()
                data_list = None
                try :
                    data_list = data_response['data']
                except Exception as e:
                    data_list = None
                if data_list != None and len(data_list) == 3 :
                    for doc in data_list :
                        name_folder = str(doc['title'])
                        if name_folder == 'Aprendiz' :
                            self.aprdz_forder_id = str(doc['id'])
                            logging.info('Carpeta Aprendiz: ' + str(self.aprdz_forder_id) ) 
                            self.get_documents( self.works_aprdz, str(self.aprdz_forder_id) )
                        if name_folder == 'Compañero' :
                            self.cmpnr_forder_id = str(doc['id'])
                            logging.info('Carpeta Companero: ' + str(self.cmpnr_forder_id) )
                            self.get_documents( self.works_cmpnr, str(self.cmpnr_forder_id) )
                        if name_folder == 'Maestro' :
                            self.mstrs_forder_id = str(doc['id'])
                            logging.info('Carpeta Maestro: ' + str(self.mstrs_forder_id) )  
                            self.get_documents( self.works_mstrs, str(self.mstrs_forder_id) )
                else :
                    logging.error('Respuesta NULA ' )
        except Exception as e:
            print("ERROR find_forders_ids():", e)

# ==============================================================================
    def get_works(self, grade_qh : int ) :
        works = []
        plans = []
        aux = []
        try :
            self.find_forders_ids()
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s and type in( 'WORK','PROGRAM' ) order by w.date desc"""
                cursor.execute(sql, str(grade_qh) )
                results = cursor.fetchall()
                for row in results:
                    if self.document_exist( str(row['namefile']), str(row['grade']) ) :
                        doc = Work( row )
                        if doc.type == 'WORK' :
                            works.append(doc)
                        if doc.type == 'PROGRAM' :
                            aux.append(doc)
                        
        except Exception as e:
            print("ERROR BD:", e)
        if aux != None and len(aux) :
            length = len(aux)
            for i in range(0, length ):
                plans.append(aux.pop()) 
        return works, plans

# ==============================================================================
    def document_exist(self, name_file : str, grade_doc : str ) :
        exist = False
        try :
            if grade_doc == '1' :
                exist = self.find_document( name_file, self.works_aprdz )
            if grade_doc == '2' :
                exist = self.find_document( name_file, self.works_cmpnr )
            if grade_doc == '3' :
                exist = self.find_document( name_file, self.works_mstrs )
        except Exception as e:
            print("ERROR document_exist():", e)
        return exist
# ==============================================================================
    def find_document(self, name_file : str, documents : list ) :
        exist = False
        for doc in documents :
            if doc['name'].lower().find(name_file.lower()) >= 0 :
                exist = True
                break
        return exist
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
                    if self.document_exist( str(row['namefile']), str(row['grade']) ) :
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

                sql = """insert into works (namefile, title, author, grade, date, type, description, small_photo) values (%s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, ( work.namefile, work.title, work.author, str(work.grade), date.strftime('%Y-%m-%d %H:%M:%S'), work.type, work.description, small_photo ) )
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

    def search_doc(self, name_file : str, folder_id : str ) :
        document_id : str = None
        try :
            logging.info('Busca pdf: ' + name_file + ' en la carpeta: ' + folder_id) 
            # primero busca en la carpeta de archivos del grado
            data_json = {
                'folder_id' : folder_id,
                'filters' : [
                    {
                        "filter_name": "title",
                        "comparation": "contains",
                        "filter_value": name_file,
                    },
                    {
                        "filter_name": "mimeType",
                        "comparation": "=",
                        "filter_value": "application/pdf",
                    }
                ],
                'only_id': True
            }
            resp = None
            url = self.url_base + '/drive/search'
            m1 = time.monotonic()
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json}), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200 or resp.status_code == 201 :
                data_response = resp.json()
                data_list = None
                try :
                    data_list = data_response['data']
                except Exception as e:
                    data_list = None
                if data_list != None :
                    if len(data_list) > 0 :
                       document_id = str(data_list[0]['id'])
        except Exception as e:
            print("ERROR serach_doc(): ", e)
        return document_id

    def get_folder_id_by_grade(self, grade : str) :
        if grade == '1' :
            return self.aprdz_forder_id
        if grade == '2' :
            return self.cmpnr_forder_id
        if grade == '3' :
            return self.mstrs_forder_id
        return None

    def get_pdf_file(self, document_grade : str, name_file : str, username : str) :
        data_base64 = None 
        mime_type = None
        try :
            self.find_forders_ids()
            id_folder : str = self.get_folder_id_by_grade(document_grade)
            if id_folder == None :
                logging.error('No se encontro la carpeta del grado: ' + document_grade )
                return data_base64, mime_type

            id_document = self.search_doc(name_file, id_folder)
            if id_document != None :
                logging.info('Documento encontrado ID: ' + str(id_document) ) 
                data_base64, mime_type = self.get_document(id_document)
        except Exception as e:
            print("ERROR get_pdf_file():", e)
        return data_base64, mime_type

    def get_document(self, id_document: str) :
        data_response = None
        mime_type = None
        try :
            logging.info('Solicita Buscar Documento ID: ' + id_document) 
            data_json = {
                'file_id' : id_document,
                'require_detail' : False,
                'require_doc' : True
            }
            resp = None
            url = self.url_base + '/drive/read'
            m1 = time.monotonic()
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json}), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200 or resp.status_code == 201 :
                data_response = resp.json()
                data_file = None
                try :
                    data_file = data_response['data']
                except Exception as e:
                    data_file = None
                if data_file != None :
                    logging.info('Documento encontrado de ' + str(data_file['size_bytes']) + ' bytes') 
                    # data_response = base64.b64decode(data_file['file_b64'])
                    data_response = data_file['file_b64']
                    mime_type = data_file['type']
                else :
                    logging.error('Respuesta NULA ' )
        except Exception as e:
            print("ERROR get_document():", e)
        
        return data_response, mime_type
    
    def get_documents(self, documents : list, folder_id : str) :
        try :
            logging.info('Solicita documentos de carpeta: ' + folder_id) 
            data_json = {
                'folder_id' : folder_id,
                'filters' : [
                    {
                        "filter_name": "mimeType",
                        "comparation": "=",
                        "filter_value": "application/pdf",
                    }
                ],
            }
            resp = None
            url = self.url_base + '/drive/list'
            m1 = time.monotonic()
            logging.info('URL: ' + url )
            resp = requests.post(url, data = json.dumps({'data': data_json}), headers = self.headers, timeout = 15)
            logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
            if resp.status_code == 200:
                data_response = resp.json()
                data_file = None
                try :
                    data_file = data_response['data']
                except Exception as e:
                    data_file = None
                if data_file != None and len(data_file) > 0 :
                    logging.info('Documento encontrados: ' + str(len(data_file))) 
                    for doc in data_file :
                        documents.append( { 'id' : doc['id'], 'name' : doc['title']} )
        except Exception as e:
            print("ERROR get_documents():", e)
# ==============================================================================

class Work() :
    id = -1
    namefile = None
    title = None
    author = None
    grade = 0
    namegrade = None
    namegr = None
    date = None
    date_hm = None
    type = None
    description = None
    small_photo = None

    def __init__(self, row ) :
        self.id = int(row['id'])
        self.title = str(row['title'])
        self.author = str(row['author'])
        self.namefile = str(row['namefile'])
        self.grade = int(row['grade'])
        self.type = str(row['type'])
        self.description = str(row['description'])
        self.small_photo = str(row['small_photo'])

        if self.grade == 1 :
            self.namegrade = 'Aprendiz'
            self.namegr = 'Primer Grado'
        elif self.grade == 2 :
            self.namegrade = 'Compañero'
            self.namegr = 'Segundo Grado'
        elif self.grade == 3 :
            self.namegrade = 'Maestro'
            self.namegr = 'Tercer Grado'
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