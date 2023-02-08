#!/bin/sh

export FLASK_APP=app
export FLASK_DEBUG=development

echo "Servidor Python de prueba" > logger.log

python3 http-server.py 8085

tail -f logger.log 