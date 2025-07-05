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
    from s3 import S3
    from drive import Drive


except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Works() :
    db : DbWork = None
    url_base : str = None
    headers = None
    util : Util = None
    s3 : S3 = None
    drive : Drive = None

    def __init__(self) :
        try:
            self.db = DbWork()
            self.util = Util()
            self.s3 = S3()
            self.drive = Drive()
        except Exception as e :
            print("ERROR Contructor Works() :", e)

    def __del__(self):
        if self.s3 != None:
            del self.s3
        if self.util != None:
            del self.util
        if self.drive != None:
            del self.drive
        if self.db != None:
            del self.db

    def upload(self, request) :
        return self.s3.upload_s3(request) 
    
    def process_drive_document(self, grade: int ) :
        self.drive.process_drive_document(str(grade))
        return
  
    def get_pdf_file(self, id_work : str, grade_doc : str = None, name_file : str = None ) :
        data_base64 = None 
        mime_type = None
        doc : Work = None
        # primero se obtiene el trabajo
        try :
            doc = self.db.search_for_id(id_work)
            # si existe localmente se entrega el PDF al toke
            if doc != None :
                data_base64 = self.util.file_exists(doc.md5sum + self.util.get_extension(doc.namefile))
                if data_base64 != None : 
                    logging.info('Documento encontrado localmente, se entrega el PDF al toke')
                    mime_type = self.util.get_mime_type(doc.namefile)
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
                data_base64, mime_type = self.s3.get_s3_document(data_json)  
            elif doc != None and doc.source == 'DRIVE' :
                logging.info('Documento \"' + doc.namefile + '\" es de Drive')
                folder = self.util.get_folders(grade_doc)[0]
                if self.drive.get_drive_document('/tmp', doc, folder) == True :
                    path_file = doc.md5sum + self.uitl.get_extension(doc.namefile)
                    data_base64 = self.util.file_exists(path_file)
                    mime_type = self.util.get_mime_type(doc.namefile)
            else :
                logging.error('Documento ' + id_work + ' no encontrado')
        except Exception as e:
            print("ERROR get_pdf_file():", e)
        return data_base64, mime_type

    def get_drive_document(self, file_path : str, name_file : str, folder : str = 'primero' ) :
        return self.drive.get_drive_document(file_path, name_file, folder)


