#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    from datetime import datetime
    import pytz 

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

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
    local_date : str = None
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

        self.fill_dates(str(row['date']))

    def fill_dates(self, str_date: str ) :
        utc_datetime = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
        self.date = utc_datetime.strftime('%d/%m/%Y')
        self.date_hm = utc_datetime.strftime('%d/%m/%Y %H:%M')
        # hora local
        chile_timezone = pytz.timezone('America/Santiago')
        chilean_time = utc_datetime.astimezone(chile_timezone)
        self.local_date = chilean_time.strftime('%d/%m/%Y %H:%M')

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
        self.local_date = None