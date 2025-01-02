#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import datetime
    import requests
    from flask_cors import CORS
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

cors = CORS(app, resources={r"/bcp/*": {"origins": ["logia.buenaventuracadiz.com"]}})
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
@app.route('/bcp/intranet/show/<path:subpath>', methods=['GET'])
@csrf.exempt
def intranet_pdf(subpath):
    user_name = None
    #base_url = str(request.headers.get('Referer'))
    #url : str = base_url + '/docs/access_denied.pdf'
    data = {
        'data'    : None,
        'type'    : 'application/pdf'
    }
    grade_docname = str(subpath)
    name = None
    logging.info('Solicita Mostrar Documento: ' + grade_docname )
    cookie = request.cookies.get('SESION_RL')
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            name = str(datos[2].strip())
        del cipher
    if user_name != None :
        logging.info('User at the cookie: ' + str(user_name))
    paths = str(grade_docname).split('/')
    if len(paths) == 2 :
        documents = Works()
        data_doc, type_doc = documents.get_url_pdf( paths[0].strip(),  paths[1].strip(), user_name )
        del documents
        if data_doc != None and type_doc != None :
            data = {
                'data'    : data_doc,
                'type'    : type_doc
            }
    return render_template( 'show.html', doc=data, name=name )

# ===============================================================================
# logout
# ===============================================================================
@app.route('/bcp/logout', methods=['GET'])
def logout():
    return redirect('/bcp/login'), 302

# ===============================================================================
# Login
# ===============================================================================
@app.route('/bcp/login', methods=['GET'])
def login():
    response = make_response( render_template( 'login.html', captcha_key=str(CAPTCHA_KEY) ) )
    response.set_cookie('SESION_RL', '', path='/bcp', max_age=0, secure=True, httponly=True )
    return response

# ===============================================================================
# VALIDATE LOGIN
# ===============================================================================
@app.route('/bcp/login/verify', methods=['POST'])
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
        security = Security()
        user, grade, name =  security.verifiy_user_pass(username, password)
        del security
    logging.info('Usuario: ' + str(name) + ' Username: ' + str(user) + ' Grado: ' + str(grade) )
    if int(grade) > 0 and int(grade) <= 3 :
        documents = Works()
        works, programs = documents.get_works(grade)
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
        cookie = str(data_cipher)
    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(minutes=5)
    # vence en 30 min
    response.set_cookie('SESION_RL', cookie, path='/bcp', max_age=1800, secure=True, httponly = True )
    return response

# ===============================================================================
# para llenar la tabla dinamicamente se deben obtener los documentos como una 
# lista de objetos con los datos necesarios para llenar la tabla
# ===============================================================================
@app.route('/bcp/intranet', methods=['GET'])
@csrf.exempt
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
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            grade = int(datos[1].strip())
            name = str(datos[2].strip())
        del cipher
    if user_name != None :
        logging.info('UserCookie[' + str(user_name)  +  ']' )
    if int(grade) > 0 and int(grade) <= 3 :
        documents = Works()
        works, programs = documents.get_works(grade)
        if works != None and programs != None :
            lengthw = len(works) 
            lengthp = len(programs)
        del documents  
    else :
        logging.info('Usuario no ha iniciado sesion')
        return redirect('/bcp/login'), 302
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
# para llenar la tabla dinamicamente se deben obtener los documentos como una 
# lista de objetos con los datos necesarios para llenar la tabla
# ===============================================================================
@app.route('/bcp/intranet/docs/<path:subpath>', methods=['GET'])
@csrf.exempt
def show_pdf(subpath):
    user_name = None
    cookie = request.cookies.get('SESION_RL')
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
        del cipher
        file_path = os.path.join(ROOT_DIR, 'static/docs')
        paths = str(subpath).split('/')
        if len(paths) == 2 :
            logging.info('Usuario: ' + str(user_name) + ' Solicita documento: ' + paths[1].strip() )
            security = Security()
            accessOk = security.access_validate(user_name, paths[0].strip())
            del security
            if accessOk :
                return send_from_directory(file_path, paths[1].strip())
    else :
        logging.info('Usuario no ha iniciado sesion')
        return redirect('/bcp/login'), 302
    return send_from_directory(file_path, 'access_denied.pdf')

# ===============================================================================
# para llenar la tabla dinamicamente se deben obtener los documentos como una 
# lista de objetos con los datos necesarios para llenar la tabla
# ===============================================================================   
@app.route('/bcp/more', methods=['GET'])
@csrf.exempt
def more():
    grade = 0
    works = []
    length = 0
    user_name = None
    grade_name = ''
    cookie = request.cookies.get('SESION_RL')
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            grade = int(datos[1].strip())
            name = str(datos[2].strip())
        del cipher
    if user_name != None :
        logging.info('UserCookie[' + str(user_name)  + ']' )
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
        works = documents.get_other_docs(grade)
        del documents  
        if works != None:
            length = len(works) 
            logging.info('Hay ' + str(length) + ' documentos adicionales para grado ' + str(grade) )
    else :
        logging.info('Usuario no ha iniciado sesion')
        return redirect('/bcp/login'), 302
      
    return render_template('more.html', grade=grade_name, documents=works, len=length, name=name )

@app.route('/bcp/youtube', methods=['GET'])
@csrf.exempt
def youtube():
    grade = 0
    grade_name = None
    user_name = None
    name = None
    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 3 :
            user_name = str(datos[0].strip())
            grade = int(datos[1].strip())
            name = str(datos[2].strip())
        del cipher
    if user_name != None :
        logging.info('UserCookie[' + str(user_name)  + ']' )
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
    else :
        return redirect('/bcp/login'), 302
    return render_template('youtube.html', grade=grade_name, name=name )

# ===============================================================================
# LOGIA
# ===============================================================================
@app.route('/bcp/home/<path:subpath>', methods=['POST','GET','PUT'])
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
@app.route('/bcp/home', methods=['GET'])
@csrf.exempt
def home():
    logging.info('HOME !!')
    return render_template( 'logia.html' )
# ===============================================================================
@app.route('/bcp/aniversario', methods=['POST','GET','PUT'])
def aniversario():
    grade = 1
    name = 'Anonimo'
    return render_template( 'aniversario.html', name=name, grade=grade )

# ===============================================================================
@app.route('/bcp/reublanca', methods=['POST','GET','PUT'])
def reublanca():
    grade = 1
    name = 'Anonimo'
    return render_template( 'reublanca.html', name=name, grade=grade )


# ==============================================================================
# Servicio para validar el recaptcha
# ==============================================================================
@app.route('/bcp/hcaptcha', methods=['POST'])
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
@app.get('/bcp/image/<path:imagen>')
@csrf.exempt
def imagenes(imagen):
    return redirect('/bcp/static/image/' + str(imagen)), 302

@app.get('/bcp/js/<path:jsfile>')
@csrf.exempt
def javascripts(jsfile):
    return redirect('/bcp/static/js/' + str(jsfile)), 302

@app.get('/bcp/styles/<path:stylesfile>')
@csrf.exempt
def stylescss(stylesfile):
    return redirect('/bcp/static/styles/' + str(stylesfile)), 302

@app.get('/bcp/static/<path:file_path>')
@csrf.exempt
def show_static_file(file_path) :
    values = file_path.split('/')
    if len(values) > 1 :
        file_path = values[0]
        name = values[1]
    else :
        name = file_path
    file_path = os.path.join(ROOT_DIR, 'static/' + str(file_path))
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
