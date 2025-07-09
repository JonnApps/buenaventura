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
    from dbwork import DbWork

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Drive() :
    db : DbWork = None
    util : Util = None
    url_base : str = None
    headers = None

    def __init__(self) :
        try:                
            api_key = str(os.environ.get('DOCS_API_KEY','None'))
            self.url_base = str(os.environ.get('API_BASE_URL','None'))
            authorization = str(os.environ.get('DOCS_API_AUTHORIZATION','None'))
            self.headers = {
                'Content-Type': 'application/json', 
                'Accept': 'application/json',
                'X-Api-Key': str(api_key), 
                'Authorization': str(authorization)
            }
            self.util = Util()
            self.db = DbWork()
        except Exception as e :
            print("ERROR Contructor Drive() :", e)

    def __del__(self):
        if self.util != None:
            del self.util
        if self.db != None:
            del self.db

    def load_drive_docs(self, grade : str ):
        name_thread = '[' + threading.current_thread().name + '-' + str(threading.get_native_id()) + '] '
        try :
            logging.info(name_thread + 'Solicita documentos de carpeta de ' + grade)
            data_json = {
                'folders' : self.util.get_folders(grade),
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
            logging.info(name_thread + 'URL: ' + url + ' Request: ' + str(data_json) )
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
                        work = self.db.search( str(doc['md5Checksum']), 'DRIVE' )
                        if work == None :
                            logging.info(name_thread + 'Se guarda en BD documento ' + str(doc['title'])) 
                            date : datetime = datetime.strptime(str(doc['createdDate']), '%Y-%m-%dT%H:%M:%S.%f%z')
                            document = Work( {
                                'id' : '-1', 
                                'title' : str(self.util.clean_text(str(doc['title']), str(doc['fileExtension']))),
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
                            w, new = self.db.save(document)
                            if w != None and new == True :
                                logging.info(name_thread + 'Documento nuevo guardado, se notifica ' )
                                self.util.notify( w )
        except Exception as e:
            print(name_thread + "ERROR load_drive_docs():", e)

    def process_drive_document(self, grade: str ) :
        self.th = threading.Thread(target=self.load_drive_docs, args=( grade ), name='th', daemon=True)
        self.th.start()

    def get_drive_document(self, path_to_save : str, doc, folder : str ) :
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
                        "filter_value": str(self.util.get_mime_type(name_file)),
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
                        success = self.util.save_doc_file( data_file['md5']+self.util.get_extension(data_file['title']), data_response )
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
