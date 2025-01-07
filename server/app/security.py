try:
    import logging
    import sys
    import os
    import time
    import json
    import requests
    from Crypto.Cipher import AES
    import base64

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Security() :
    root_dir = None
    headers = None
    url_base = 'https://dev.jonnattan.com/scraper'
    def __init__(self, root_dir = str(ROOT_DIR)) :
        try:
            self.root_dir = root_dir
            api_key = str(os.environ.get('LOGIA_SCRAPER_API_KEY','None'))
            authorization = str(os.environ.get('LOGIA_SCRAPER_AUTHORIZATION','None'))
            self.headers = {
                'Content-Type': 'application/json', 
                'Accept': 'application/json',
                'X-Api-Key': str(api_key), 
                'Authorization': str(authorization)
            }
        except Exception as e :
            print("ERROR :", e)
            self.api_key = None
            self.root_dir = None
    #================================================================================================
    # verificaci'on de usuarios 
    #================================================================================================
    def verifiy_user_pass( self, username, password ) :
        logging.info("Rescato password para usuario: " + str(username) )
        url = self.url_base + '/logia/login'
        user = 'Desconocido'
        grade = 0
        name = None
        maintainer = False
        message = 'Error de ejecución del servicio'
        try :
            if len(str(user)) > 0 and len(str(password)) > 0 :
                m1 = time.monotonic()
                cipher = Cipher()
                dato = username + '|||' + password
                data_cipher = cipher.aes_encrypt( dato )
                data_json = {
                    'data' : str(data_cipher)
                }
                resp = None
                logging.info("URL: " + url )
                resp = requests.post(url, data = json.dumps(data_json), headers = self.headers, timeout = 60)
                logging.info('Response ' + str( time.monotonic() - m1 )  + ' seg' )
                if resp.status_code == 200 or resp.status_code == 201 :
                    data_response = resp.json()
                    user = str( data_response['user'] )
                    grade = int( data_response['grade'] ) 
                    name = 'Qh:. ' + str( data_response['name'] ) 
                    message = str(data_response['message']) 
                    maintainer = bool(data_response['maintainer'])
            else :
                logging.info('No cumplen con largos username['+str(username)+'] o pass['+str(password)+']')
        except Exception as e:
            print("ERROR POST:", e)
        return user, grade, name, maintainer
    #================================================================================================
    # Obtengo el grado del QH
    #================================================================================================
    def get_grade( self, username ) :
        logging.info('Intento obtener grado de ' + str(username) )
        url = self.url_base + '/logia/usergl/grade'
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
            resp = requests.post(url, data = json.dumps(data_json), headers = self.headers, timeout = 5)
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
    def access_validate(self, username, grade) :
        access = False
        logging.info('Valido acceso a recurso de ' + str(grade) + ' a ' + str(username) )
        url = self.url_base + '/logia/usergl/access'
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
            resp = requests.post(url, data = json.dumps(data_json), headers = self.headers, timeout = 40)
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


class Cipher() :
    aes_key = None
    iv = None

    def __init__(self, ) :
        key = os.environ.get('AES_KEY','None')
        self.aes_key = key.encode('utf-8')[:32]
        self.iv = b'1234567890123456'

    def __del__(self):
        self.aes_key = None
        self.iv = None

    def complete( self, data_str : str ) :
        response : str = data_str
        if data_str != None :
            length = len(data_str)
            resto = 16 - (length % 16)
            i = 0
            while i < resto :
                response += " "
                i += 1
        return response.encode()

    def aes_encrypt(self, payload : str ) :  
        data_cipher_str = None
        try :
            data_clear = self.complete(payload) # se lleva a bytes el texto
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
            data_cipher = cipher.encrypt(data_clear) # se encriptan los bytes
            if data_cipher != None :
                b64 = base64.b64encode(data_cipher) # se convierten en base64
                data_cipher_str = b64.decode() # pasan a string la cadena de bytes
        except Exception as e:
            print("ERROR Cipher:", e)
            data_cipher_str = None
        return data_cipher_str

    def aes_decrypt(self, data_cipher_str: str ) :        
        data_clear_str = None
        try :
            b64 = data_cipher_str.encode() # string se pasan a bytes
            data_cipher = base64.b64decode(b64) # bytes en base64 se pasan a los bytes para decifrar
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
            data_clear = cipher.decrypt(data_cipher) # se desencriptan los bytes
            if data_clear != None :
                data_clear_str = data_clear.decode() # se llega la cadeba de bytes a texto
                data_clear_str = data_clear_str.strip()
        except Exception as e:
            print("ERROR Decipher:", e)
            data_clear_str = None
        return data_clear_str
    