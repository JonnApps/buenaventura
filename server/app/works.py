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
except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


class Works() :
    db = None
    host = 'dev.jonnattan.com'
    user = 'logia'
    password = 'RL188#2022'
    database = 'gral-purpose'

# ==============================================================================
    def __init__(self) :
        self.connect()
# ==============================================================================
    def __del__(self):
        if self.db != None:
            self.db.close()
# ==============================================================================
    def connect( self ) :
        try:
            if self.db == None :
                self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database,cursorclass=pymysql.cursors.DictCursor)
        except Exception as e :
            print("ERROR BD:", e)
            self.db = None
# ==============================================================================
    def isConnect(self) :
        return self.db != None
# ==============================================================================
    def getWorks(self, grade ) :
        works = []
        plans = []
        aux = []
        try :
            if self.isConnect() :
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

    def getOtherDocs(self, grade ) :
        works = []
        try :
            if self.isConnect() :
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