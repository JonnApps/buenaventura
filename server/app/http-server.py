#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    from datetime import datetime
    import requests
    from flask_cors import CORS
    from flask_wtf.csrf import CSRFProtect
    from flask import Flask, render_template, make_response, request, redirect, jsonify, send_from_directory
    # Clases personales
    from security import Security, Cipher
    from check import Checker
    from works import Works
    from work import Work
    from dbwork import DbWork
    from util import Util

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
    data = {
        'data'    : None,
        'type'    : 'application/pdf'
    }
    name_qh = None
    maintainer = False
    cookie = request.cookies.get('SESION_RL')
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            user_name = str(datos[0].strip())
            grade_qh = int(datos[1].strip())
            name_qh = str(datos[2].strip())
            maintainer = bool(datos[3].strip())
            logging.info('User at the cookie: ' + str(user_name) + ', grade ' + str(grade_qh) + ', maintainer ' + str(maintainer) )
        # array del path que trae el nombre, grado e id del doc
        paths = str(subpath).split('/')
        logging.info('Solicita Mostrar Documento: ' + str(subpath) + ', Length: ' + str(len(paths)) )
        if len(paths) == 3 :
            documents = Works()
            data_doc, type_doc = documents.get_pdf_file(paths[0].strip(), paths[1].strip(), paths[2].strip())
            del documents
            if data_doc != None and type_doc != None :
                data = {
                    'data'    : data_doc,
                    'type'    : type_doc
                }
    return render_template( 'show.html', doc=data, name=name_qh, maintainer=maintainer, user_name=user_name), 200

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
    grade_qh : int = 0
    name_qh : str = 'QH:. Sin Nombre'
    user = None
    works = []
    programs = []
    lengthw = 0
    lengthp = 0
    maintainer = False
    if username != None and password != None :
        security = Security()
        user, grade_qh, name_qh, maintainer =  security.verifiy_user_pass(username, password)
        del security
    logging.info('Usuario: ' + str(name_qh) + ' Username: ' + str(user) + ' Grado: ' + str(grade_qh) + ' Mantenedor: ' + str(maintainer) )
    if grade_qh > 0 and grade_qh <= 3 :
        db = DbWork()
        works, programs = db.get_works(grade_qh)
        del db  
        if works != None and programs != None :
            lengthw = len(works) 
            lengthp = len(programs)
    data = {
        'works' : works,
        'lengthw' : lengthw,
        'programs' : programs,
        'lengthp' : lengthp,
        'grade' : grade_qh,
        'name' : name_qh,
        'maintainer' : bool(maintainer),
        'username' : username
    }
    logging.info('Data for intranet: ' + str(data) )

    response = make_response( render_template('intranet.html', data = data ) )
    cookie : str = ''
    if user != None and grade_qh > 0 and grade_qh <= 3 :
        cipher = Cipher()
        dato = str(username) + '&' + str(grade_qh) + '&' + str(name_qh) + '&' + str(maintainer)
        data_cipher = cipher.aes_encrypt( dato )
        del cipher
        cookie = str(data_cipher)
    
    # cookie vence en 30 min
    response.set_cookie('SESION_RL', cookie, path='/bcp', max_age=1800, secure=True, httponly = True )
    return response

# ===============================================================================
# para llenar la tabla dinamicamente se deben obtener los documentos como una 
# lista de objetos con los datos necesarios para llenar la tabla
# ===============================================================================
@app.route('/bcp/intranet', methods=['GET'])
def intranet():
    works = []
    programs = []
    user_name = None
    grade_qh : int = 0
    name_qh = None 
    maintainer : bool = False
    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            user_name = str(datos[0].strip())
            grade_qh = int(datos[1].strip())
            name_qh = str(datos[2].strip())
            maintainer = bool(datos[3].strip())
            logging.info('User at the cookie: ' + str(user_name) + ', grade ' + str(grade_qh) + ', maintainer ' + str(maintainer) )
    else :
        return redirect('/bcp/login'), 302

    if grade_qh > 0 and grade_qh <= 3 :
        db = DbWork()
        works, programs = db.get_works(grade_qh)
        del db  
        util = Util()
        logging.info('There are ' + str(len(works) + len(programs)) + ' works at ' + str(grade_qh) + ' grade ' )
        del util
    else :
        return redirect('/bcp/login'), 302

    data = {
        'works' : works,
        'lengthw' : len(works),
        'programs' : programs,
        'lengthp' : len(programs),
        'grade' : grade_qh,
        'name' : name_qh,
        'maintainer' : maintainer,
        'username' : user_name
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
        if len(datos) == 4 :
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
    grade_qh : int = 0
    works = []
    length = 0
    user_name = None
    grade_name : str = ''
    maintainer : bool = False
    name_qh : str = None
    cookie = request.cookies.get('SESION_RL')
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 4 :
            user_name = str(datos[0].strip())
            grade_qh = int(datos[1].strip())
            name_qh = str(datos[2].strip())
            maintainer = bool(datos[3].strip())
            logging.info('User at the cookie: ' + str(user_name) + ', grade ' + str(grade_qh) + ', maintainer ' + str(maintainer) )
        del cipher
    else :
        return redirect('/bcp/login'), 302
    util = Util()
    grade_name = util.get_name(grade_qh)
    del util
    if grade_name != None :
        bd = DbWork()
        works = bd.get_additional_works(grade_qh)
        del bd
        work = Works()
        work.process_drive_document(grade_qh)
        del work
        if works != None:
            logging.info('Hay ' + str(len(works)) + ' documentos adicionales para grado ' + str(grade_qh) )
        
        data = {
            'works' : works,
            'length' : len(works),
            'grade' : grade_name,
            'name' : name_qh,
            'maintainer' : maintainer,
            'username' : user_name
        }
    else :
        return redirect('/bcp/login'), 302
      
    return render_template('more.html', data=data )

@app.route('/bcp/maintainer', methods=['GET'])
def maintainer():
    user_param : str = request.args.get('user', 'none')
    grade_qh : int = 0
    grade_name : str = None
    user_name : str = None
    name_qh : str = None
    works : list = []
    length : int = 0
    cookie = request.cookies.get('SESION_RL')
    data = {}
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            documents = Works()
            works = documents.get_all_docs()
            del documents  
            data = {
                'user_name' : str(datos[0].strip()),
                'grade_qh': int(datos[1].strip()),
                'name_qh': str(datos[2].strip()),
                'maintainer': bool(datos[3].strip()),
                'works' : works,
                'length' : len(works)
            }
            logging.info('User at the cookie: ' + str(data['user_name']) + ', grade ' + str(data['grade_qh']) + ', maintainer ' + str(data['maintainer']) )
    else :
        return redirect('/bcp/login'), 302

    if user_param == data['user_name'] and data['maintainer'] == True and data['grade_qh'] == 3 :
        return render_template('maintainer.html', data = data, captcha_key=str(CAPTCHA_KEY) )
    else :
        return redirect('/bcp/login'), 302

@app.route('/bcp/work/del/<path:id>', methods=['GET'])
def del_work( id ):  
    msg : str = 'Archivo eliminado correctamente'  
    cookie = request.cookies.get('SESION_RL')
    data = {}
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            user_name = str(datos[0].strip())
            grade_qh = int(datos[1].strip())
            name_qh = str(datos[2].strip())
            maintainer = bool(datos[3].strip())
            logging.info('User at the cookie: ' + user_name + ', grade ' + str(grade_qh) + ', maintainer ' + str(maintainer) )
            if maintainer and grade_qh == 3 :
                documents = Works()
                success = documents.delete( int(id) )
                works : list = []
                if success :
                    works = documents.get_all_docs()
                else :
                    msg = 'Error eliminando archivo, intente nuevamente'
                del documents  
                data = {
                    'user_name' : user_name,
                    'grade_qh': grade_qh,
                    'name_qh':name_qh,
                    'maintainer': maintainer,
                    'works' : works,
                    'length' : len(works)
                }
    return render_template('maintainer.html', data = data, captcha_key=str(CAPTCHA_KEY), msg=msg)


@app.route('/bcp/work/upload', methods=['POST'])
@csrf.exempt
def upload_work(): 
    cookie = request.cookies.get('SESION_RL')
    data_response = {'md5' : '', 'filename' : ''}
    status_code = 200
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            data_cookie = {
                'user_name' : str(datos[0].strip()),
                'grade_qh': int(datos[1].strip()),
                'name_qh': str(datos[2].strip()),
                'maintainer': bool(datos[3].strip()),
            }
            work = Works()
            data_response, status_code = work.upload(request)
            del work
            logging.info('User at the cookie: ' + str(data_cookie['user_name']) + ', grade ' + str(data_cookie['grade_qh']) + ', maintainer ' + str(data_cookie['maintainer']) )
    return jsonify(data_response), status_code

@app.route('/bcp/work/add', methods=['POST'])
def add_work(): 
    msg : str = 'Archivo agregado correctamente'  
    date : datetime = None
    try :
        d = str(request.form['date'])
        h = str(request.form['hour'])
        if len(h) == 0 :
            h = '00:00'
        date_str = d + ' ' + h + ':00'
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        logging.info('Date: ' + str(date))
    except Exception as e :
        logging.error(e)
        date = datetime.now()
        logging.info('Date: Now() ')

    grade_doc : str = '1'
    try :
        if request.form['grade'] != None :
            grade_doc = str(request.form['grade'])
    except Exception as e :
        logging.error(e)
        grade_doc = '1'
    
    logging.info('Form: ' + str(request.form) )

    work = Work(
        {
            'id' : -1,
            'title' : str(request.form['title']),
            'author' : 'QH:. ' + str(request.form['author']),
            'namefile' : str(request.form['namefile']),
            'grade' : int(grade_doc),
            'type' : str(request.form['type']),
            'date' : date.strftime('%Y-%m-%d %H:%M:%S'),
            'description' : str(request.form['description']),
            'md5sum' : str(request.form['md5doc']),
            'source' : 'S3',
            # 'url': str(request.form['url']),
            'small_photo' : None,
        }
    )
    
    cookie = request.cookies.get('SESION_RL')
    data = {}
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            user_name = str(datos[0].strip())
            grade_qh = int(datos[1].strip())
            name_qh = str(datos[2].strip())
            maintainer = bool(datos[3].strip())
            logging.info('User at the cookie: ' + user_name + ', grade ' + str(grade_qh) + ', maintainer ' + str(maintainer) )
            if maintainer and grade_qh == 3 :
                documents = Works()
                success = documents.save( work )
                works : list = []
                if success != None :
                    works = documents.get_all_docs()
                else :
                    msg = 'Error agregando archivo, intente nuevamente'
                del documents  
                data = {
                    'user_name' : user_name,
                    'grade_qh': grade_qh,
                    'name_qh':name_qh,
                    'maintainer': maintainer,
                    'works' : works,
                    'length' : len(works)
                }
    return render_template('maintainer.html', data = data, captcha_key=str(CAPTCHA_KEY), msg=msg)

@app.route('/bcp/youtube', methods=['GET'])
def youtube():
    grade_qh : int = 0
    grade_name : str = None
    user_name : str = None
    name_qh : str = None
    cookie = request.cookies.get('SESION_RL')

    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        datos = data_str.split('&')
        if len(datos) == 4 :
            user_name = str(datos[0].strip())
            grade_qh = int(datos[1].strip())
            name_qh = str(datos[2].strip())
            maintainer = bool(datos[3].strip())
            logging.info('User at the cookie: ' + str(user_name) + ', grade ' + str(grade_qh) + ', maintainer ' + str(maintainer) )
        del cipher
    else :
        return redirect('/bcp/login'), 302
    util = Util()
    grade_name = util.get_name(grade_qh)
    del util
    if grade_name == None :
        return redirect('/bcp/login'), 302
    return render_template('youtube.html', grade=grade_name, name=name_qh, maintainer=maintainer, username=user_name)

# ===============================================================================
# LOGIA
# ===============================================================================
@app.route('/bcp/home/<path:subpath>', methods=['POST','GET','PUT'])
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
def home():
    cookie = request.cookies.get('SESION_RL')
    data = {}
    if cookie != None :
        cipher = Cipher()
        data_str = cipher.aes_decrypt(cookie)
        del cipher
        datos = data_str.split('&')
        if len(datos) == 4 :
            data = {
                'user_name' : str(datos[0].strip()),
                'grade_qh': int(datos[1].strip()),
                'name_qh': str(datos[2].strip()),
                'maintainer': bool(datos[3].strip()),
            }
            logging.info('User at the cookie: ' + str(data['user_name']) + ', grade ' + str(data['grade_qh']) + ', maintainer ' + str(data['maintainer']) )
    return render_template( 'logia.html', data=data )
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
    name_file : str = None
    if len(values) > 1 :
        name_file = values[len(values) - 1]
        file_path = file_path.replace(name_file, '')
    else :
        name_file = file_path
    file_path = os.path.join(ROOT_DIR, 'static/' + str(file_path))
    logging.info("Static File: " + str( file_path ) )
    if not os.path.exists(file_path + str(name_file)) :
        logging.info('Archivo no encontrado: ' + str( file_path ) + str(name_file) )
        work = Works()
        success = work.get_drive_document(file_path, name_file)
        del work
        if success :
            logging.info('Archivo ' + str( file_path ) + str(name_file) + ' descargado...'  )

    return send_from_directory(file_path, str(name_file))

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
