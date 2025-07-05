#!/usr/bin/python

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
    from util import Util

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class S3() :
    util : Util = None
    headers = None
    url_base : str = None

    def __init__(self) :
        try:
            authorization = str(os.environ.get('DOCS_API_AUTHORIZATION','None'))
            api_key = str(os.environ.get('DOCS_API_KEY','None'))
            self.url_base = str(os.environ.get('API_BASE_URL','None'))
            self.headers = {
                'Content-Type': 'application/json', 
                'Accept': 'application/json',
                'X-Api-Key': str(api_key), 
                'Authorization': str(authorization)
            }
            self.util = Util()
        except Exception as e :
            print("ERROR Contructor S3() :", e)

    def __del__(self):
        if self.util != None:
            del self.util

    def upload_s3(self, request) :
        data_response = { 'md5': None, 'message': 'Servicio ejecutado exitosamente', 'size': 0 }
        http_code : int = 201
        m1 = time.monotonic()
        file_path : str = None
        try :
            request_data = request.get_json()
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
                    self.util.save_doc_file( data_file['md5'] + self.util.get_extension(data_json['data']['name_file']), data_response )
                else :
                    logging.error('Respuesta NULA ' )
        except Exception as e:
            print("ERROR get_s3_document():", e)
        
        return data_response, mime_type
