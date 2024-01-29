try:
    import logging
    import sys
    import os
    import time
    import json
    import requests
    from jose import jwe

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

class Security() :
    api_key = os.environ.get('APIKEY_SERVER','None')
    #================================================================================================
    # verificaci'on de usuarios 
    #================================================================================================
    def verifiyUserPass( self, username, password ) :
        logging.info("Rescato password para usuario: " + str(username) )
        url = 'https://dev.jonnattan.com/logia/usergl/login'
        headers = {'API-Key': str(self.api_key), 'Content-Type': 'application/json' }
        user = 'Desconocido'
        grade = 0
        name = None
        message = 'Error de ejecución del servicio'
        try :
            if len(str(user)) > 0 and len(str(password)) > 0 :
                m1 = time.monotonic()
                cipher = Cipher()
                dato = username + '|||' + password
                data_cipher = cipher.aes_encrypt( dato )
                data_json = {
                    'data' : str(data_cipher.decode('UTF-8'))
                }
                resp = None
                logging.info("POST To URL: " + url )
                resp = requests.post(url, data = json.dumps(data_json), headers = headers, timeout = 60)
                diff = time.monotonic() - m1;
                logging.info('Response ' + str( diff )  + ' seg' )
                if resp.status_code == 200 or resp.status_code == 201 :
                    data_response = resp.json()
                    user = str( data_response['user'] )
                    grade = str( data_response['grade'] ) 
                    name = str( data_response['name'] ) 
                    message = data_response['message'] 
            else :
                logging.info('No cumplen con largos username['+str(username)+'] o pass['+str(password)+']')
        except Exception as e:
            print("ERROR POST:", e)
        logging.info(' Message: [' + str( message ) +'] User[' + user + ']' )
        return user, grade, name
    #================================================================================================
    # Obtengo el grado del QH
    #================================================================================================
    def getGrade( self, username ) :
        logging.info('Intento obtener grado de ' + str(username) )
        url = 'https://dev.jonnattan.com/logia/usergl/grade'
        headers = {'API-Key': str(self.api_key), 'Content-Type': 'application/json' }
        grade = 0
        try :
            m1 = time.monotonic_ns()
            cipher = Cipher()
            dato = str(username)
            data_cipher = cipher.aes_encrypt( dato )
            data_json = {
                'user' : str(data_cipher.decode('UTF-8'))
            }
            resp = None
            logging.info("POST To URL: " + url )
            resp = requests.post(url, data = json.dumps(data_json), headers = headers, timeout = 5)
            diff = time.monotonic_ns() - m1;
            logging.info('Response ' + str( diff )  + ' nanoseg' )
            if resp.status_code == 200 :
                data_response = resp.json()
                grade = int(str( data_response['grade'] ))
            logging.info("Response Message: " + str( data_response['message'] ) )
        except Exception as e:
            print("ERROR POST:", e)
            grade = 0

        return grade

    #================================================================================================
    # Valido el grado del QH logeado con el del documento que desea ver
    #================================================================================================
    def accessValidate(self, username, grade) :
        access = False
        logging.info('Valido acceso a recurso de ' + str(grade) + ' a ' + str(username) )
        url = 'https://dev.jonnattan.com/logia/usergl/access'
        headers = {'API-Key': str(self.api_key), 'Content-Type': 'application/json' }
        try :
            m1 = time.monotonic_ns()
            cipher = Cipher()
            dato = str(username) + '&&' + str(grade)
            data_cipher = cipher.aes_encrypt( dato )
            data_json = {
                'data' : str(data_cipher.decode('UTF-8'))
            }
            resp = None
            logging.info("POST To URL: " + url )
            resp = requests.post(url, data = json.dumps(data_json), headers = headers, timeout = 40)
            diff = time.monotonic_ns() - m1;
            logging.info('Response ' + str( diff )  + ' nanoseg' )
            if resp.status_code == 200 :
                data_response = resp.json()
                code = int(str( data_response['code'] ))
                access = code == 4500
            logging.info("Response Message: " + str( data_response['message'] ) )
        except Exception as e:
            print("ERROR POST:", e)

        return access

    #================================================================================================
    # Obtiene la URL del documento PDF
    #================================================================================================
    def getUrlPdf( self, grade, namedoc, user ) :
        logging.info('Intento obtener documento ' + str(namedoc) )
        url = 'https://dev.jonnattan.com/logia/docs/url'
        headers = {'API-Key': str(self.api_key), 'Content-Type': 'application/json' }
        doc_url = ''
        try :
            m1 = time.monotonic_ns()
            cipher = Cipher()
            dato = str(namedoc)+ ';' + str(grade) + ';' + str(user)
            data_cipher = cipher.aes_encrypt( dato )
            data_json = {
                'data' : str(data_cipher.decode('UTF-8'))
            }
            resp = None
            logging.info("POST To URL: " + url )
            resp = requests.post(url, data = json.dumps(data_json), headers = headers, timeout = 40)
            diff = time.monotonic_ns() - m1 
            logging.info('Response HTTP_' + str( resp.status_code )  + ' en ' + str( diff )  + ' nanoseg' )
            if resp.status_code == 200 :
                data_response = resp.json()
                doc_url = str( data_response['url'] )
                dato = str( data_response['data'] ) # es un dato cifrado
                doc_url = doc_url + dato
                logging.info("Response URL: " + str( doc_url ) )
                
        except Exception as e:
            print("ERROR POST:", e)
            doc_url = ''

        return doc_url


class Cipher() :
    aes_key = ''
    algorithm = ''

    def __init__(self, algorithm='aes', aes_key=None ) :
        self.id = id
        self.aes_key = aes_key
        if aes_key == None :
            self.aes_key =  str(os.environ.get('AES_KEY','NO_CAPTCHA_KEY')) # 256 bit
        self.algorithm = algorithm

    def __del__(self):
        self.aes_key = ''
        self.algorithm = ''

    def aes_encrypt(self, payload ) :
        data_cipher = None
        try :
            logging.info("Cifro: " + str(self.algorithm))
            data_cipher = jwe.encrypt(payload, key=self.aes_key, algorithm='dir', encryption='A256GCM')
        except Exception as e:
            print("ERROR Cipher:", e)
            data_cipher = None
        return data_cipher

    def aes_decrypt(self, data ) :
        data_clear = None
        try :
            logging.info("Decifro" + str(self.algorithm))
            data_clear = jwe.decrypt(data, key=self.aes_key )
        except Exception as e:
            print("ERROR Decipher:", e)
            data_clear = None
        return data_clear