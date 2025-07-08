try:
    import logging
    import sys
    import os
    import time
    import requests
    import json
    from dbwork import DbWork

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

class Checker() :

    def getInfo(self) :
        m1 = time.monotonic()
        url = 'https://dev.jonnattan.com/ckeckall'
        headers = { 'authorization': 'Basic Y2hlY2s6Y2hlY2sxMjMj','accept-encoding': 'gzip, deflate','content-length': '0'}
        status = 500
        logging.info("Check Conection Status to Jonnattan Server" )
        data_response = {'message': 'Error interno' }
        try :
            db = DbWork()
            db.update_past_works()
            del db             
            data_response = {'message': 'Todo Ok' }
            status = 200
        except Exception as e:
            print("ERROR POST:", e)
        diff = time.monotonic() - m1;
        logging.info("Response in " + str(diff) + " sec")
        
        return data_response, status
