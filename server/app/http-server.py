#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import requests
    import json
    import pymysql.cursors
    from datetime import datetime, timedelta
    from flask_cors import CORS
    from flask_httpauth import HTTPBasicAuth
    from flask import Flask, render_template, abort, make_response, request, redirect, jsonify, send_from_directory
    # Clases personales
    from security import Security
    from check import Checker
    from works import Works

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

############################# Configuraci'on de Registro de Log  ################################
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
# Log en pantalla
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
fh = logging.FileHandler('logger.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
# se meten ambas configuraciones
root.addHandler(handler)
root.addHandler(fh)

logger = logging.getLogger('HTTP')
# ==============================================================================
# COnfiguraciones generales del servidor Web
# ==============================================================================
app = Flask(__name__)
auth = HTTPBasicAuth()
cors = CORS(app, resources={r"/*": {"origins": "*"}})
# ==============================================================================
# variables globales
# ==============================================================================
ROOT_DIR = os.path.dirname(__file__)

#===============================================================================
# Redirige
#===============================================================================
@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/info'), 302

#===============================================================================
# Redirige
#===============================================================================
@app.route('/<path:subpath>', methods=('GET', 'POST'))
def processOtherContext( subpath ):
    return redirect('/info'), 302

#===============================================================================
# Redirige a mi blog personal
#===============================================================================
@app.route('/info', methods=['GET', 'POST'])
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
@app.route('/checkall', methods=['GET', 'POST'])
@auth.login_required
def checkProccess():
    checker = Checker()
    json = checker.getInfo()
    del checker
    return jsonify(json)

# ===============================================================================
# INTRANET
# ===============================================================================
@app.route('/intranet/show/<path:subpath>', methods=['GET'])
@auth.login_required
def intranet_pdf(subpath):
    request_data = request.headers.get('Referer')
    base_url =  str(request_data)
    url = base_url + '/docs/access_denied.pdf'
    grade_docname = str(subpath)
    logging.info('Solicita Mostrar Documento: ' + grade_docname )
    username = auth.current_user()
    paths = str(grade_docname).split('/')
    if len(paths) == 2 :
        sec = Security()
        url = sec.getUrlPdf( paths[0].strip(),  paths[1].strip(), username )
        del sec 
    if url == '' :
        url = base_url + '/docs/access_denied.pdf'
    return render_template( 'show.html', doc=url )
# ===============================================================================
@app.route('/intranet/docs/<path:subpath>', methods=['GET'])
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
# para llenar la tabla dinamicamente se deben obtener los documentos como una 
# lista de objetos con los datos necesarios para llenar la tabla
# ===============================================================================
@app.route('/intranet', methods=['GET'])
@auth.login_required
def intranet():
    grade = 0
    works = []
    programs = []
    lenProgram = 0
    length = 0
    username = auth.current_user()
    sec = Security()
    grade = sec.getGrade(username)
    logging.info('Solicito los docs guadados de grado: ' + str(grade) )
    del sec
    if int(grade) > 0 and int(grade) <= 3 :
        documents = Works()
        works, programs = documents.getWorks(grade)
        if works != None and programs != None :
            length = len(works) 
            lenProgram = len(programs)
            logging.info('Hay ' + str(length) + ' trabajos para grado ' + str(grade) )
        del documents    
    return render_template('intranet.html', grade=grade, documents=works, len=length, programs=programs, len_programs = lenProgram )

@app.route('/more', methods=['GET'])
@auth.login_required
def more():
    grade = 0
    works = []
    length = 0
    username = auth.current_user()
    sec = Security()
    grade = sec.getGrade(username)
    grade_name = None
    logging.info('Solicito los docs guadados de grado: ' + str(grade) )
    del sec
    if int(grade) >= 1 and int(grade) <= 3 :
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

@app.route('/youtube', methods=['GET'])
@auth.login_required
def youtube():
    grade = 0
    username = auth.current_user()
    sec = Security()
    grade = sec.getGrade(username)
    grade_name = None
    del sec
    logging.info('Acceso a videos de grado ' + str(grade) )
    if int(grade) >= 1 and int(grade) <= 3 :
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
@app.route('/home/<path:subpath>', methods=['POST','GET','PUT'])
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
@app.route('/home', methods=['POST','GET','PUT'])
def rl_aniversario_home():
        return render_template( 'logia.html' )

# ===============================================================================
# imagenes estaticas del sistema
# ===============================================================================
@app.route('/static/image/<path:name>', methods=['GET'])
def show_image(name):
    imagen = str(name)
    logging.info('Solicita imagen: ' + imagen)
    file_path = os.path.join(ROOT_DIR, 'static/image')
    return send_from_directory(file_path, imagen)

# ===============================================================================
# Favicon
# ===============================================================================
@app.route('/favicon.ico', methods=['POST','GET','PUT'])
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
        app.run( host='0.0.0.0', port=listenPort, debug=True)
    except Exception as e:
        print("ERROR MAIN:", e)

    logging.info("PROGRAM FINISH")
