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

class DbWork() :
    db = None
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

        except Exception as e :
            print("ERROR Contructor DbWork() :", e)
    # ==============================================================================
    # destructor
    # ==============================================================================
    def __del__(self):
        if self.db != None:
            self.db.close()
    # ==============================================================================
    # Verifica la conexion a la base de datos
    # ==============================================================================
    def is_connect(self) :
        return self.db != None
    # ==============================================================================
    # obtiene los trabajos que se han registrado en la base de datos como los que vienen
    # y los que son presentes esta semana
    #SELECT column1, column2, ... FROM your_table WHERE conditions ORDER BY some_column LIMIT limit OFFSET (page - 1) * limit;
    # ==============================================================================
    def get_works(self, grade_qh : int, page : int, limit : int, type_work : str = 'WORK' ) :
        works : list = []
        try :
            offset : int = (page - 1) * limit
            logging.info('Se obtienen los trabajos ' + type_work + ' del grado ' + str(grade_qh) + ' Page: ' + str(page) + ' LIMIT ' + str(limit) + ' OFFSET ' + str(offset) ) 
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """select * from works w where grade <= %s and type = %s order by w.date desc limit %s offset %s"""
                cursor.execute(sql, (str(grade_qh), type_work, limit, offset, ) )
                results = cursor.fetchall()
                for row in results:
                    works.append( Work( row ))
            else :
                logging.error('No hay conexion a la BD')
        except Exception as e:
            print("ERROR get_works():", e)
        return works

    def update_past_works(self, ) :
        try :
            logging.info('Se actualizan los trabajos ya presentados...' ) 
            if self.is_connect() :
                cursor = self.db.cursor()
                sql = """update works w set type = 'WORK' where w.type='PROGRAM' and w.date < now()"""
                cursor.execute(sql)
                self.db.commit()
                logging.info('Actualización OK...' ) 
            else :
                logging.error('No hay conexion a la BD')
        except Exception as e:
            print("ERROR update_past_works():", e)
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
                sql = """select * from works w where grade <= %s order by w.id desc"""
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
        is_new : bool = False
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
                        is_new = False
                else:
                    logging.info('Insertando el trabajo: ' + work.namefile )
                    sql = """insert into works (namefile, title, author, grade, date, type, description, small_photo, md5sum, source) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql, ( work.namefile, work.title, work.author, str(work.grade), date.strftime('%Y-%m-%d %H:%M:%S'), work.type_work, work.description, small_photo, work.md5sum, work.source ) )
                    self.db.commit()
                    is_new = True
                saved = self.search(work.md5sum, work.source)  
        except Exception as e:
                print("ERROR save():", e)
        return saved, is_new
    # ==============================================================================
    # Se obtiene el objeto de la base de datos con el campo md5sum y fuente
    # ==============================================================================
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
    # ==============================================================================
    # Se obtiene el objeto de la base de datos
    # ==============================================================================
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
    # ==============================================================================
    # Elimina el trabajo de la base de datos
    # ==============================================================================
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