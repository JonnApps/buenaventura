FROM python:3

LABEL VERSION=1.0
LABEL DESCRIPCION="Python Server HTTP"

RUN pip install --upgrade pip && \
    pip3 install requests && \
    pip3 install pyopenssl  && \
    pip3 install flask && \
    pip3 install PyMySQL && \
    pip3 install datetime && \
    pip3 install flask_httpauth && \
    pip3 install python-jose && \
    pip3 install flask-cors && \
    pip3 install boto3 && \
    mkdir -p /usr/src/app

EXPOSE 8085

COPY ./app/run.sh /usr/src/app/run.sh

WORKDIR /usr/src/app

CMD [ "/bin/sh", "./run.sh" ]
