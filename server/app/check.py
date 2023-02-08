try:
    import logging
    import sys
    import os
    import time
    import json
    import pymysql.cursors
    from datetime import datetime, timedelta

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

class Checker() :
    db = None
    host = 'localhost'
    user = 'logia'
    password = 'RL188#2022'
    database = 'gral-puspose'
    table = 'secure'

    def __init__(self) :
        try:
            self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database,cursorclass=pymysql.cursors.DictCursor)
        except Exception as e :
            print("ERROR BD:", e)
            self.db = None

    def __del__(self):
        if self.db != None:
            self.db.close()

    def isConnect(self) :
        return self.db != None

    def getInfo(self) :
        m1 = time.monotonic()
        logging.info("Check Status All Components" )
        status_bd = self.isConnect()

        time_response = time.monotonic() - m1
        data = {
            'Server'    : 'dev.jonnattan.com',
            'Owner'     : 'Jonnattan Griffiths Catalan',
            'Linkedin'  : 'https://www.linkedin.com/in/jonnattan',
            'Web'       : 'https://dev.jonnattan.com',
            'Files'     : data != None,
            'Data Base' : status_bd,
            'Time'      : time_response
        }
        logging.info("Response in " + str(time_response) + " ms")
        return data
