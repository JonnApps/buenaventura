try:
    import logging
    import sys
    import os
    import time
    import requests
    import json

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
        data_response = {'message': 'Error interno Gw' }
        try :
            resp = None
            logging.info("POST To URL: " + url )
            resp = requests.get(url, data = json.dumps({}), headers = headers, timeout = 40)
            status = resp.status_code
            logging.info("HTTP Response: " + str(resp.status_code) )
            if resp.status_code == 200 :
                data_response = {'message': 'Conexion Ok' }
            
        except Exception as e:
            print("ERROR POST:", e)
        diff = time.monotonic_ns() - m1;
        logging.info("Response in " + str(diff) + " ms")
        
        return data_response, status
