from repositories import Repositories

class Services:

	def getApiLogin(self):

		apiLoginRepo = Repositories()
		token = apiLoginRepo.apiLogin()

		return token


	def getDocumentsData(self, token, id_entrega):

		getDataRepo = Repositories()
		data = getDataRepo.getDocumentsData(token, id_entrega)

		return data


	def updateDocumentoEstado(self, url, token, famracia, nro_receta):

		updateDocumentoEstadoRepo = Repositories()
		response = updateDocumentoEstadoRepo.updateDocumentoEstado(url, token, famracia, nro_receta)

		return response

	
	def verificar(self, fecha1, fecha2, id_farmacia):

		repositories = Repositories()
		data = repositories.verificar(fecha1, fecha2, id_farmacia)

		return data


	def verificar_count(self, fecha1, fecha2, id_farmacia):

		repositories = Repositories()
		data = repositories.verificar_count(fecha1, fecha2, id_farmacia)

		return data