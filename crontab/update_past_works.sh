#!/bin/sh

cd /home/jonnattan/source/buenaventura/crontab
echo "[INFO] --------- Actualizando past_works" > ./logs/update_past_works.log
curl --location 'https://logia.buenaventuracadiz.cl/checksystem'
echo "[INFO] --------- Actualizado: $(date)" >> ./logs/update_past_works.log