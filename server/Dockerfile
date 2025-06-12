FROM python:3.13-slim

LABEL VERSION=1.1
LABEL DESCRIPCION="Logia Server"

# variables importantes
ARG CAPTCHA_KEY
ARG AES_KEY
ARG SECRET_KEY_CSRF

ENV FLASK_APP app

RUN addgroup --gid 10101 logia && \
    adduser --home /home/logia --uid 10100 --gid 10101 --disabled-password logia

USER logia  

COPY requirements.txt /home/logia/requirements.txt

RUN cd /home/logia && \ 
    mkdir -p /home/logia/.local/bin && \
    export PATH=$PATH:/home/logia/.local/bin && \
    pip install --upgrade pip && \
    pip install -r requirements.txt 

WORKDIR /home/logia/app

EXPOSE 58085

CMD [ "python", "http-server.py", "58085"]
