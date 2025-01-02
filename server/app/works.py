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
    host = '192.168.0.15'
    user = 'logia'
    port = 3306
    password = 'RL188#2022'
    database = 'gral-purpose'
    url_base = 'https://dev.jonnattan.com/docs'
    headers = None
    folder_docs : str = 'docs'

# ==============================================================================
    def __init__(self) :
        self.connect()
        self.folder_docs = str(os.environ.get('DRIVER_FOLDER_ID','None'))
        api_key = str(os.environ.get('DOCS_API_KEY','None'))
        authorization = str(os.environ.get('DOCS_API_AUTHORIZATION','None'))
        self.headers = {
            'Content-Type': 'application/json', 
            'Accept': 'application/json',
            'X-Api-Key': str(api_key), 
            'Authorization': str(authorization)
        }
# ==============================================================================
    def __del__(self):
        if self.db != None:
            self.db.close()
# ==============================================================================
    def connect( self ) :
        try:
            if self.db == None :
                self.db = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database,cursorclass=pymysql.cursors.DictCursor)
        except Exception as e :
            print("ERROR BD:", e)
            self.db = None
# ==============================================================================
    def is_connect(self) :
        return self.db != None
# ==============================================================================
    def get_works(self, grade ) :
        works = []
        plans = []
        aux = []
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s and type in( 'WORK','PROGRAM' ) order by w.date desc"""
                cursor.execute(sql, str(grade) )
                results = cursor.fetchall()
                for row in results:
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

    def get_other_docs(self, grade ) :
        works = []
        try :
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s and type = 'ADDITIONAL' order by w.date desc"""
                cursor.execute(sql, str(grade) )
                results = cursor.fetchall()
                for row in results:
                    doc = Work( row )
                    works.append(doc)
        except Exception as e:
            print("ERROR BD:", e)
        return works

    def get_url_pdf(self, grade: str, namefile : str, username : str) :
        data_base64 = None 
        mime_type = None
        try :
            logging.info('Solicita Buscar Documento: ' + namefile) 
            # primero busca en la carpeta de archivos del grado
            data_json = {
                'folder_id' : self.folder_docs,
                'file_name' : namefile
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
                       id_document = data_list[0]['id']
                       logging.info('Documento encontrado ID: ' + str(id_document) ) 
                       data_base64, mime_type = self.get_document(id_document)
                else :
                    logging.error('Respuesta NULA ' )
        except Exception as e:
            print("ERROR BD:", e)
        return data_base64, mime_type

    def get_document(self, id_document: str) :
        data_response = None
        mime_type = None
        try :
            logging.info('Solicita Buscar Documento ID: ' + id_document) 
            data_json = {
                'file_id' : id_document,
                'only_read' : False,
                'base64' : True
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