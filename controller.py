from datetime import date, datetime, timedelta
import threading
import json, re, time, os, random
from os.path import exists
import pandas as pd
from io import BytesIO as IO
from services import Services
from flask import Flask, request, Response, render_template, redirect, flash, url_for, jsonify, redirect
from flask import current_app
import pathlib


def login():
	servicesLoginApi = Services()
	token = servicesLoginApi.getApiLogin()

	return (token)


def get_documents(token, id_entrega):
	servicesGetData = Services()
	data = servicesGetData.getDocumentsData(token, id_entrega)

	return (data)


def update_documents(token, iddocumento, farmacia, nro_receta):
	id_app = str(353)
	url = "https://api.nosconecta.com.ar:443/metadata/"+id_app+"/"+str(iddocumento)

	
	servicesMetaData = Services()
	response = servicesMetaData.updateDocumentoEstado(url, token, farmacia, nro_receta)

	return (response)


def task(app, all_list):
	with app.app_context():
		"""
		background Process handled by Threads
		:return: None
		"""
		print("Started Task ...")
		print(threading.current_thread().name)


		token = login()

		

		for r0w in all_list:

			"""
			if r0w['iddocumento'] == '6547520':
				print(r0w['iddocumento'])
				print(r0w['entrega_id'])
				response_tsdocs = update_documents(token, r0w['iddocumento'], '', '')
				#print(response_tsdocs)
				response = response_tsdocs.status_code
				print(response)
			"""
			#print(r0w['entrega_id'])
			response_tsdocs = update_documents(token, r0w['iddocumento'], r0w['farmacia'], r0w['nro_receta'])
			response = response_tsdocs.status_code

		time.sleep(6)
		print("completed .....")




class Controller:


	def __init__(self):

		self.dir_path = os.path.dirname(os.path.realpath(__file__))


	def generate_json(self, json_object, json_name):
		# generate json file
		with open(json_name, "w") as outfile:
			outfile.write(json_object)
		#print('- JSON File generated')


	def get_json(self, json_name, nro_farma):
		if os.path.exists(self.dir_path):
			if exists(json_name):
				data = json.load(open(json_name))
				for p_id in data:
					u_id = p_id.get('id')
					if(u_id == nro_farma):
						data = p_id.get('default')
						# dosomthing
				return data



	def view(self, nro):

		if nro == '1': farmacia_title = 'FARMACIA SCIENZA PUEYRREDON'
		elif nro == '2': farmacia_title = 'F SCIENZA GUEMES'
		elif nro == '3': farmacia_title = 'F SCIENZA PELLEGRINI'
		else: return redirect('/recetas/farmacia/1')
		
		return render_template("recetas/index.html", farma=farmacia_title, limit_date=date.today()-timedelta(days=1))

	def view2(self, sap_count, d1, d2, farma_title, default_number):

		return render_template("recetas/index2.html", sap_count=sap_count, d1=d1, d2=d2, farma=farma_title, default_number=default_number)

	

	def populate_sap(self, results, nro_receta, sap_count):
		# data loop
		columns = [
					'nombre_campo',
					'estado_nuevo',
					'id_documento_mod_pos',
					'id_documento_mod_cab',
					'fe_modif',
					'num_entrega',
					'destinatario_merc',
					'estado_entrega',
					'destino',
					'letra',
					'interlocutor',
					'farmacia'
				]
		data=[]
		z=int(sap_count)
		x=int(nro_receta)
		for res in results:
			item = {}
			for i, r in enumerate(res):
				if (columns[i] == columns[5]):
					item[columns[i]] = res[i].lstrip('0')
				else:
					item[columns[i]] = res[i]
			item['nro_receta'] = x
			#print(item)
			data.append(item)
			x=x+1
		if not data:
			return 500
		else:
			return data



	def generate_excel(self, response_data_sap, no_list):


		dat=[]
		for ro in response_data_sap:
			lista={}
			for key in ro.keys():
				if(key == 'nro_receta'):lista['Nro de Receta']=ro['nro_receta']
				if(key == 'nombre_campo'):lista['Nombre Campo']=ro['nombre_campo']
				if(key == 'estado_nuevo'):lista['Estado Nuevo']=ro['estado_nuevo']
				if(key == 'id_documento_mod_pos'):lista['Id Documento Mod Pos']=ro['id_documento_mod_pos']
				if(key == 'id_documento_mod_cab'):lista['Id Documento Mod Cab']=ro['id_documento_mod_cab']
				if(key == 'fe_modif'):lista['Fe Modif']=ro['fe_modif']
				if(key == 'num_entrega'):lista['Numero de Entrega']=ro['num_entrega']
				if(key == 'destino'):lista['Destino']=ro['destino']
				if(key == 'letra'):lista['Letra']=ro['letra']
				if(key == 'interlocutor'):lista['Interlocutor']=ro['interlocutor']
				if(key == 'farmacia'):lista['Farmacia']=ro['farmacia']
			for val in ro.values():
				for r in no_list:
					if (r['nro_receta'] == ro['nro_receta']):
						val='TSDOCS not found'
					else:
						val=ro['nro_receta']
			dat.append(lista)

		dat = json.dumps(dat)
		dat = json.loads(dat)


		date_time = datetime.now()
		date = datetime.strftime(date_time, '%Y%m%d')
		name = 'recetas_'+str(date)+'_'+str("{:06x}".format(random.randint(0, 0xFFFFFF)))+'.xlsx'

		# this is my output data a list of lists
		df_output = pd.DataFrame(dat)

		# my "Excel" file, which is an in-memory output file (buffer) 
		# for the new workbook
		excel_file = IO()

		xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')

		df_output.to_excel(xlwriter, 'sheetname')

		xlwriter.save()
		#xlwriter.close()

		# important step, rewind the buffer or when it is read() you'll get nothing
		# but an error message when you try to open your zero length file in Excel
		excel_file.seek(0)

		# set the mime type so that the browser knows what to do with the file
		response = Response(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

		# set the file name in the Content-Disposition header
		response.headers.set("Content-Disposition", "attachment", filename=name)

		return (response)


	def data(self, fecha1, fecha2, farma_title):
		if fecha1 != None and fecha1 != '' or fecha2 != None and fecha2 != '':
			if farma_title == 'FARMACIA SCIENZA PUEYRREDON': nro_farma = '0084000753'
			elif farma_title == 'F SCIENZA GUEMES': nro_farma = '0084000484'
			elif farma_title == 'F SCIENZA PELLEGRINI': nro_farma = '0084011182'
			services = Services()
			data_sap_count = services.verificar_count(fecha1.replace('-', ''),fecha2.replace('-', ''),nro_farma)
			data_sap_count = str(data_sap_count[0])

			default_number = self.get_json('/app/default_number.json', nro_farma) 
			
			return self.view2(data_sap_count, fecha1, fecha2, farma_title, default_number)

		else:
			return redirect('/recetas/farmacia/1')

	def data2(self, fecha1, fecha2, nro_receta, farma_title, sap_count):
		if fecha1 != None and fecha1 != '' or fecha2 != None and fecha2 != '':
			if farma_title == 'FARMACIA SCIENZA PUEYRREDON': nro_farma = '0084000753'
			elif farma_title == 'F SCIENZA GUEMES': nro_farma = '0084000484'
			elif farma_title == 'F SCIENZA PELLEGRINI': nro_farma = '0084011182'
			services = Services()
			data_sap = services.verificar(fecha1.replace('-', ''),fecha2.replace('-', ''),nro_farma)
			response_data_sap = self.populate_sap(data_sap, nro_receta, sap_count)


			token = login()


			unique = { each['num_entrega'] : each for each in response_data_sap }.values()

			all_list = []
			no_list = []
			for ro in unique:

				data = get_documents(token, ro['num_entrega'])

				if data['results'] and data['results'] != None and data['results'] != '' :

					for re in data['results']:

						if re['id'] == '' and re['entrega_id'] != '':

							no_data = {
								'entrega_id' : re['entrega_id'],
								'farmacia' : ro['farmacia'],
								'nro_receta' : ro['nro_receta']
							}

							no_list.append(no_data)
							
							print('ID DOC NOT FOUND')
							print(re['entrega_id'])

						else:

							if (re['id'] != '' and re['entrega_id'] != ''):


								list_data = {
									'iddocumento' : re['id'],
									'entrega_id' : re['entrega_id'],
									'farmacia' : ro['farmacia'],
									'nro_receta' : ro['nro_receta']
								}

								all_list.append(list_data)


			app = current_app._get_current_object()
			threading.Thread(target=task, args=[app, all_list] ).start()


			response = self.generate_excel(response_data_sap, no_list)

			response_sap = response_data_sap.pop()
			list_value = list(response_sap.values())
			nro_receta = int(list_value[12])+1

			with open('/app/default_number.json', 'r+') as f:
				data = json.load(f)
				for row in data:
					if row['id'] == nro_farma:
						row['default'] = nro_receta # <--- add `id` value.
					f.seek(0)        # <--- should reset file position to the beginning.
					json.dump(data, f, indent=4)
					f.truncate()     # remove remaining part



			return (response)

		else:
			return redirect('/recetas/farmacia/1')

	"""
	def data_1(self, fecha1, fecha2, nro_receta):
		if fecha1 != None and fecha1 != '' or fecha2 != None and fecha2 != '':
			services = Services()
			data_sap = services.verificar(fecha1.replace('-', ''),fecha2.replace('-', ''),'0084000753')
			response_data_sap = self.populate_sap(data_sap, nro_receta)
			app = current_app._get_current_object()
			threading.Thread(target=task, args=[app, response_data_sap] ).start()

			response = self.generate_excel(response_data_sap)
			return (response)

		else:
			return redirect('/recetas/farmacia/1')
	"""