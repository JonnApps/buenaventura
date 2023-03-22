#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import datetime
    import requests
    from flask_cors import CORS
    from flask_httpauth import HTTPBasicAuth
    from flask_wtf.csrf import CSRFProtect
    from flask import Flask, render_template, make_response, request, redirect, jsonify, send_from_directory
    # Clases personales
    from security import Security, Cipher
    from check import Checker
    from works import Works

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:',
       str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

# ===================== Configuraci'on de Registro de Log ======================
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
# Log en pantalla
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
#fh = logging.FileHandler('logger.log')
#fh.setLevel(logging.INFO)
#fh.setFormatter(formatter)
# se meten ambas configuraciones
root.addHandler(handler)
#root.addHandler(fh)

logger = logging.getLogger('HTTP')
# ==============================================================================
# COnfiguraciones generales del servidor Web
# ==============================================================================

CAPTCHA_KEY = os.environ.get('CAPTCHA_KEY','NO_CAPTCHA_KEY')
CAPTCHA_SECRET = os.environ.get('CAPTCHA_SECRET','NO_CAPTCHA_SECRET')
SECRET_KEY_CSRF = os.environ.get('SECRET_KEY_CSRF','KEY-CSRF-ACA-DEBE-IR')

app = Flask(__name__)
app.config.update( DEBUG=False, SECRET_KEY = str(SECRET_KEY_CSRF), )

csrf = CSRFProtect()
csrf.init_app(app)

auth = HTTPBasicAuth( )
cors = CORS(app, resources={r"/page/*": {"origins": ["logia.buenaventuracadiz.com"]}})
# ==============================================================================
# variables globales
# ==============================================================================
ROOT_DIR = os.path.dirname(__file__)

#===============================================================================
# Redirige
#===============================================================================
@app.route('/', methods=['GET', 'POST'])
@csrf.exempt
def index():
    return redirect('/info'), 302

#===============================================================================
# Redirige
#===============================================================================
@app.route('/<path:subpath>', methods=('GET', 'POST'))
@csrf.exempt
def processOtherContext( subpath ):
    return redirect('/info'), 302

#===============================================================================
# Redirige a mi blog personal
#===============================================================================
@app.route('/info', methods=['GET', 'POST'])
@csrf.exempt
def infoJonnaProccess():
    logging.info("Reciv solicitude endpoint: /infojonna" )
    return jsonify({
        "Servidor": "logia.buenaventuracadiz.com",
        "Telefono": "(+56) 9 9211 6678",
        "Valle":"Viña del Mar"
    })
#===============================================================================
# Metodo solicitado por la biblioteca de autenticaci'on b'asica
#===============================================================================
@auth.verify_password
def verify_password(username, password):
    user = None
    if username != None and password != None :
        basicAuth = Security()
        user =  basicAuth.verifiyUserPass(username, password)
        del basicAuth
    return user

#===============================================================================
# Implementacion del handler que respondera el error en caso de mala autenticacion
#===============================================================================
@auth.error_handler
def unauthorized():
    return render_template('more.html', grade=None ), 401
    # return make_response(jsonify(data), 401)


#===============================================================================
# Se checkea el estado del servidor completo para reportar
#===============================================================================
@app.route('/checksystem',  methods=('GET', 'POST'))
@csrf.exempt
def checkProccess():
    checker = Checker()
    json, status = checker.getInfo()
    del checker
    return jsonify(json), status

# ===============================================================================
# INTRANET
# ===============================================================================
@app.route('/page/intranet/show/<path:subpath>', methods=['GET'])
@csrf.exempt
@auth.login_required
def intranet_pdf(subpath):
    user_name = None
    request_data = request.headers.get('Referer')
    base_url =  str(request_data)
    url = base_url + '/docs/access_denied.pdf'
    grade_docname = str(subpath)
    logging.info('Solicita Mostrar Documento: ' + grade_docname )
    
    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_clear = cipher.aes_decrypt(cookie)
        data_str = str(data_clear.decode('UTF-8'))
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
        del cipher
    
    
    auth_user = auth.current_user()
    if( auth_user != None and user_name != None ) :
        logging.info('UserCookie[' + str(user_name)  + '] UserAuth[' + str(auth_user[0]) +']' )


    paths = str(grade_docname).split('/')
    if len(paths) == 2 :
        sec = Security()
        url = sec.getUrlPdf( paths[0].strip(),  paths[1].strip(), user_name )
        del sec 
    if url == '' :
        url = base_url + '/docs/access_denied.pdf'
    return render_template( 'show.html', doc=url )
# ===============================================================================
# LOGIN
# ===============================================================================
@app.route('/page/login', methods=['GET'])
def login():
    logging.info('LOGIN!!')
    return render_template( 'login.html', captcha_key=str(CAPTCHA_KEY) )

# ===============================================================================
# VALIDATE LOGIN
# ===============================================================================
@app.route('/page/login/verify', methods=['POST'])
def login_verify():
    username = str(request.form['username'])
    password = str(request.form['password'])
    grade = 0
    name = 'QH:. Sin Nombre'
    user = None
    works = []
    programs = []
    lengthw = 0
    lengthp = 0

    if username != None and password != None :
        basic_auth = Security()
        user, grade, name =  basic_auth.verifiyUserPass(username, password)
        del basic_auth
    logging.info('Username['+str(user)+'] Grado['+str(grade)+'] Usuario['+str(name)+']' )
    if int(grade) > 0 and int(grade) <= 3 :
        documents = Works()
        works, programs = documents.getWorks(grade)
        if works != None and programs != None :
            lengthw = len(works) 
            lengthp = len(programs)
        del documents  
    data = {
        'works' : works,
        'lengthw' : lengthw,
        'programs' : programs,
        'lengthp' : lengthp,
        'grade' : int(grade),
        'name' : name
    }
    response = make_response( render_template('intranet.html', data = data ) )
    
    cookie = ''
    if username != None and grade != None :
        cipher = Cipher()
        dato = str(username) + '&' + str(grade) + '&' + str(name)
        data_cipher = cipher.aes_encrypt( dato )
        cookie = str(data_cipher.decode('UTF-8'))

    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(minutes=5)
    # vence en 30 min
    response.set_cookie('SESION_RL', cookie, path='/page', max_age=1800 )

    return response

# ===============================================================================
# para llenar la tabla dinamicamente se deben obtener los documentos como una 
# lista de objetos con los datos necesarios para llenar la tabla
# ===============================================================================
@app.route('/page/intranet', methods=['GET'])
@csrf.exempt
@auth.login_required
def intranet():
    works = []
    programs = []
    user_name = None
    grade = 0
    name = None 
    lengthw = 0
    lengthp = 0

    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_clear = cipher.aes_decrypt(cookie)
        data_str = str(data_clear.decode('UTF-8'))
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            grade = int(datos[1].strip())
            name = str(datos[2].strip())
        del cipher
    
    auth_user = auth.current_user()
    if( auth_user != None and user_name != None ) :
        logging.info('UserCookie[' + str(user_name)  + '] UserAuth[' + str(auth_user[0]) +']' )

    if( auth_user != None and cookie == None ) :
        if int(grade) == str(auth_user[1]) and str(auth_user[0]) == user_name and int(grade) == 0:
            sec = Security()
            grade = sec.getGrade(auth_user)
            logging.info('Solicito los docs guadados de grado: ' + str(grade) )
            del sec

    if int(grade) > 0 and int(grade) <= 3 :
        documents = Works()
        works, programs = documents.getWorks(grade)
        if works != None and programs != None :
            lengthw = len(works) 
            lengthp = len(programs)
        del documents  
    
    logging.info('Hay ' + str(lengthw + lengthp) + ' trabajos para ' + str(name) )

    data = {
        'works' : works,
        'lengthw' : lengthw,
        'programs' : programs,
        'lengthp' : lengthp,
        'grade' : int(grade),
        'name' : name
    }

    return render_template('intranet.html', data = data )

# ===============================================================================
# ===============================================================================
@app.route('/page/intranet/docs/<path:subpath>', methods=['GET'])
@csrf.exempt
def show_pdf(subpath):
    file_path = os.path.join(ROOT_DIR, 'static/docs')
    paths = str(subpath).split('/')
    if len(paths) == 2 :
        username = auth.current_user()
        logging.info('Usuario: ' + str(username) + ' Solicita documento: ' + paths[1].strip() )
        sec = Security()
        accessOk = sec.accessValidate(username, paths[0].strip())
        del sec
        if accessOk :
            return send_from_directory(file_path, paths[1].strip())
    return send_from_directory(file_path, 'access_denied.pdf')


# ===============================================================================
@app.route('/page/more', methods=['GET'])
@csrf.exempt
@auth.login_required
def more():
    grade = 0
    works = []
    length = 0
    user_name = None
    grade_name = ''
    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_clear = cipher.aes_decrypt(cookie)
        data_str = str(data_clear.decode('UTF-8'))
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            grade = int(datos[1].strip())
            name = str(datos[2].strip())
        del cipher

    auth_user = auth.current_user()
    
    if( auth_user != None and user_name != None ) :
        logging.info('UserCookie[' + str(user_name)  + '] UserAuth[' + str(auth_user[0]) +']' )

    if( auth_user != None and cookie == None ) :
        if int(grade) == str(auth_user[1]) and str(auth_user[0]) == user_name and int(grade) == 0:
            sec = Security()
            grade = sec.getGrade(auth_user)
            logging.info('Solicito los docs guadados de grado: ' + str(grade) )
            del sec


    if int(grade) > 0 and int(grade) <= 3 :
        if int(grade) == 1 :
            grade_name = 'Primer Grado'
        elif int(grade) == 2 :
            grade_name = 'Segundo Grado'
        elif int(grade) == 3 :
            grade_name = 'Tercer Grado'
        else :
            grade_name = None
        documents = Works()
        works = documents.getOtherDocs(grade)
        if works != None:
            length = len(works) 
            logging.info('Hay ' + str(length) + ' documentos adicionales para grado ' + str(grade) )
        del documents    
    return render_template('more.html', grade=grade_name, documents=works, len=length )

@app.route('/page/youtube', methods=['GET'])
@csrf.exempt
@auth.login_required
def youtube():
    grade = 0
    grade_name = None
    user_name = None

    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_clear = cipher.aes_decrypt(cookie)
        data_str = str(data_clear.decode('UTF-8'))
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            grade = int(datos[1].strip())
            name = str(datos[2].strip())
        del cipher

    auth_user = auth.current_user()
    if( auth_user != None and user_name != None ) :
        logging.info('UserCookie[' + str(user_name)  + '] UserAuth[' + str(auth_user[0]) +']' )

    if( auth_user != None and cookie == None ) :
        if int(grade) == str(auth_user[1]) and str(auth_user[0]) == user_name and int(grade) == 0:
            sec = Security()
            grade = sec.getGrade(auth_user)
            logging.info('Solicito los docs guadados de grado: ' + str(grade) )
            del sec

    logging.info('Acceso a videos de grado ' + str(grade) )
    if int(grade) > 0 and int(grade) <= 3 :
        if int(grade) == 1 :
            grade_name = 'Primer Grado'
        elif int(grade) == 2 :
            grade_name = 'Segundo Grado'
        elif int(grade) == 3 :
            grade_name = 'Tercer Grado'
        else :
            grade_name = None
    return render_template('youtube.html', grade=grade_name )

# ===============================================================================
# LOGIA
# ===============================================================================
@app.route('/page/home/<path:subpath>', methods=['POST','GET','PUT'])
@csrf.exempt
def rl_aniversario(subpath):
    path = str(subpath)
    logging.info('Solicita Path: /' + path)
    if path == 'buenaventura.png' :
        file_path = os.path.join(ROOT_DIR, 'static')
        file_path = os.path.join(file_path, 'image')
        return send_from_directory(file_path, 'buenaventura.png')
    else :
        return render_template( 'logia.html', select=path )
# ===============================================================================
@app.route('/page/home', methods=['GET'])
@csrf.exempt
def home():
    logging.info('HOME !!')
    return render_template( 'logia.html' )
# ===============================================================================
@app.route('/page/agape', methods=['POST','GET','PUT'])
def agape():
    return render_template( 'agape.html' )


# ==============================================================================
# Servicio para validar el recaptcha
# ==============================================================================
@app.route('/page/hcaptcha', methods=['POST'])
@csrf.exempt
def validatehcaptcha( ):
    logging.info("Reciv Header : " + str(request.headers) )
    logging.info("Reciv Data: " + str(request.data) )
    request_data = request.get_json()
    response = str(request_data['response'])
    secret = str(CAPTCHA_SECRET)
    sitekey = str(CAPTCHA_KEY)
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    diff = 0
    m1 = time.monotonic()
    data_response = {}
    code = 409
    if response != None and secret != None and sitekey != None:
        url = 'https://hcaptcha.com/siteverify'
        datos = {'secret': secret,'response': response,'sitekey': sitekey }
        logging.info("URL : " + url + ' datos: ' + str(datos) )
        resp = requests.post(url, data = datos, headers = headers, timeout = 40)
        diff = time.monotonic() - m1
        code = resp.status_code
        if( code == 200 ) :
            logging.info("Response OK: " + str( resp ) )
            data_response = resp.json()
            logging.info("Response OK: " + str( data_response ) )
        else :
            logging.info("Response NOK: " + str( resp ) )
    
    logging.info("Time Response in " + str(diff) + " sec." )

    return jsonify(data_response), code
# ===============================================================================
# Archivos est'aticos del sistema
# ===============================================================================
@app.route('/static/<path:folder>/<path:name>', methods=['GET'])
@csrf.exempt
def show_static_file(folder, name):
    logging.info('Solicita a ' + str(folder) + ' archivo: ' + str(name))
    file_path = os.path.join(ROOT_DIR, 'static/' + str(folder))
    return send_from_directory(file_path, str(name))

# ===============================================================================
# Favicon
# ===============================================================================
@app.route('/favicon.ico', methods=['POST','GET','PUT'])
@csrf.exempt
def favicon():
    file_path = os.path.join(ROOT_DIR, 'static')
    file_path = os.path.join(file_path, 'image')
    return send_from_directory(file_path,
            'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ===============================================================================
# Metodo Principal que levanta el servidor
# ===============================================================================
if __name__ == "__main__":
    listenPort = 8085
    logger.info("ROOT_DIR: " + ROOT_DIR)
    logger.info("ROOT_DIR: " + app.root_path)
    if(len(sys.argv) == 1):
        logger.error("Se requiere el puerto como parametro")
        exit(0)
    try:
        logger.info("Server listen at: " + sys.argv[1])
        listenPort = int(sys.argv[1])
        # app.run(ssl_context='adhoc', host='0.0.0.0', port=listenPort, debug=True)
        # app.run( ssl_context=('cert_jonnattan.pem', 'key_jonnattan.pem'), host='0.0.0.0', port=listenPort, debug=True)
        app.run( host='0.0.0.0', port=listenPort)
    except Exception as e:
        print("ERROR MAIN:", e)

    logging.info("PROGRAM FINISH")
