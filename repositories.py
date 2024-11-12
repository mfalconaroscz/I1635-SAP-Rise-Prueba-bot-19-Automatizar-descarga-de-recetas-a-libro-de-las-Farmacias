#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, shlex, subprocess
import urllib.request, http.client, socket, requests
import os, ssl
from flask import current_app as app
import logging
import jaydebeapi
import MySQLdb
from requests.packages.urllib3.exceptions import InsecureRequestWarning


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): 
	ssl._create_default_https_context = ssl._create_unverified_context



class Repositories:

	def __init__(self):

		# Api Data Production
		self.url_auth = 'ENDPOINT'
		self.user = 'MAIL'
		self.password = 'PWD'

		# Database Connection SAP SERVER
		self.dirverSap=app.config['DRIVER_SAP']
		self.jarFileSap=app.config['JAR_FILE_SAP']
		self.urlSap=app.config['URL_SAP']
		self.DBUserSap=app.config['DB_USER_SAP']
		self.DBPwdSap=app.config['DB_PWD_SAP']


	def apiLogin(self):
		# These lines enable debug logging; remove them once everything works.
		logging.basicConfig(level=logging.INFO)

		# GET/auth
		headers = {
			'Accept' : 'application/json',
			'user' : self.user,
			'password' : self.password
		}
		res = requests.request('GET', self.url_auth, headers=headers, verify=False)
		return res.json()['message']['token']



	def getDocumentsData(self, token, id_entrega):

		url = 'https://api.nosconecta.com.ar:443/search/353?filter=%5B%7B%22key%22%3A%22entrega_id%22%2C%22value%22%3A%22'+str(id_entrega)+'%22%7D%5D'
		logging.basicConfig(level=logging.INFO)
		# GET/auth
		headers = {
			'Accept' : 'application/json',
			'Authorization' : 'Bearer '+token,
			'Accept': '*/*',
			'Accept-Encoding' : 'gzip, deflate, br',
			'Content-Type' : 'application/json; charset=utf-8',
			'Connection': 'keep-alive'
		}
		cmd = """curl -X GET '%s' -k -H 'accept: application/json' -H 'Authorization: Bearer %s' """ % (url, token)
		#print(cmd)
		args = shlex.split(cmd)
		process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		
		res = json.loads(stdout.decode("utf-8"))

		#print(res['message']['total'])
		#print(res['message']['page'])
		#print(res['message']['bypage'])

		return res['message']



	def updateDocumentoEstado(self, url, token, farmacia, nro_receta):

		# These lines enable debug logging; remove them once everything works.
		logging.basicConfig(level=logging.INFO)
		# GET/auth
		headers = {
			'Accept' : 'application/json',
			'Authorization' : 'Bearer '+token
		}

		data = {
			"farmacia_scienza" : farmacia,
			"nro_receta" : nro_receta
		}

		#response=''
		#print(url)
		#print(data)

		response = requests.put(url,headers=headers,stream=True,data=data,verify=False) 
		json_content = response.json()
		
		return (response)



	def verificar(self, fecha1, fecha2, id_farmacia):
		
		# These lines enable debug logging; remove them once everything works.
		logging.basicConfig(level=logging.INFO)

		connSap = jaydebeapi.connect(self.dirverSap, self.urlSap, [self.DBUserSap, self.DBPwdSap], self.jarFileSap)

		######## DATABASE SAP ########
		querySap = """
			SELECT DISTINCT \
			CDPOS.FNAME AS NOMBRE_CAMPO, \
			CDPOS.VALUE_NEW AS ESTADO_NUEVO, \
			CDPOS.CHANGENR AS ID_DOCUMENTO_MOD_POS, \
			CDHDR.CHANGENR AS ID_DOCUMENTO_MOD_CAB, \
			CDHDR.UDATE AS FE_MODIF, \
			CDHDR.OBJECTID AS NUM_ENTREGA, \
			LIKP.KUNNR AS DESTINATARIO_MERC, \
			LIKP.ZZESTADO AS ESTADO_ENTREGA, \
			LIKP.ZZDESTINO AS DESTINO, \
			LIKP.ZZLETRA AS LETRA, \
			VBPA.KUNNR AS INTERLOCUTOR, \
			KNA1.NAME1 AS FARMACIA \
			FROM (CDPOS \
			INNER JOIN CDHDR ON CDHDR.OBJECTID = CDPOS.OBJECTID AND CDHDR.CHANGENR = CDPOS.CHANGENR AND CDHDR.OBJECTCLAS = CDPOS.OBJECTCLAS \
			INNER JOIN LIKP ON LIKP.VBELN = CDPOS.OBJECTID \
			INNER JOIN LIPS ON LIPS.VBELN = LIKP.VBELN \
			INNER JOIN VBAP ON VBAP.VBELN = LIPS.VGBEL AND VBAP.POSNR = LIPS.VGPOS \
			INNER JOIN VBAK ON VBAK.VBELN = VBAP.VBELN \
			INNER JOIN VBPA ON VBPA.VBELN = LIKP.VBELN \
			INNER JOIN KNA1 ON KNA1.KUNNR = VBPA.KUNNR) \
			WHERE CDPOS.FNAME = 'ZZESTADO' \
			AND CDPOS.VALUE_NEW = '18' \
			AND VBPA.PARVW = 'ZD' \
			AND VBAK.VTWEG = '10' \
			AND CDHDR.UDATE BETWEEN '%s' AND '%s' \
			AND VBPA.KUNNR = '%s' \
		""" % (fecha1, fecha2, id_farmacia)
		
		curs = connSap.cursor()
		curs.execute(querySap)
		response = curs.fetchall()
		curs.close()
		
		return (response)



	def verificar_count(self, fecha1, fecha2, id_farmacia):
		
		# These lines enable debug logging; remove them once everything works.
		logging.basicConfig(level=logging.INFO)

		connSap = jaydebeapi.connect(self.dirverSap, self.urlSap, [self.DBUserSap, self.DBPwdSap], self.jarFileSap)

		######## DATABASE SAP ########
		querySap = """
			SELECT \
			COUNT(DISTINCT CDHDR.OBJECTID) \
			FROM (CDPOS \
			INNER JOIN CDHDR ON CDHDR.OBJECTID = CDPOS.OBJECTID AND CDHDR.CHANGENR = CDPOS.CHANGENR AND CDHDR.OBJECTCLAS = CDPOS.OBJECTCLAS \
			INNER JOIN LIKP ON LIKP.VBELN = CDPOS.OBJECTID \
			INNER JOIN LIPS ON LIPS.VBELN = LIKP.VBELN \
			INNER JOIN VBAP ON VBAP.VBELN = LIPS.VGBEL AND VBAP.POSNR = LIPS.VGPOS \
			INNER JOIN VBAK ON VBAK.VBELN = VBAP.VBELN \
			INNER JOIN VBPA ON VBPA.VBELN = LIKP.VBELN \
			INNER JOIN KNA1 ON KNA1.KUNNR = VBPA.KUNNR) \
			WHERE CDPOS.FNAME = 'ZZESTADO' \
			AND CDPOS.VALUE_NEW = '18' \
			AND VBPA.PARVW = 'ZD' \
			AND VBAK.VTWEG = '10' \
			AND CDHDR.UDATE BETWEEN '%s' AND '%s' \
			AND VBPA.KUNNR = '%s' \
		""" % (fecha1, fecha2, id_farmacia)
		
		curs = connSap.cursor()
		curs.execute(querySap)
		response = curs.fetchone()
		curs.close()
		
		return (response)