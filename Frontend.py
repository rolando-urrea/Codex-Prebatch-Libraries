def analyzeBarcode(barcode):
	# Determines the id and string quality from the barcode.
	# Two formats are supported: with or without parentheses.
	# With them, the number of letters must be 44; without, 36.
	# Case A (parentheses) format: (240)1819695(10)0001821150(15)181014(90)0085; (240) productId[char * 7] (10) batch[char * 10] (15) expirationDate[char * 6] (90) serial[char * 4].
	# Case B (no parentheses) format: 240181969510000182115015181014900085; 240 productId[char * 7] 10 batch[char * 10] 15 expirationDate[char * 6] 90 serial[char * 4].
	# This function will return a string for logging purposes. It must add the elements from the barcode to the auxiliary table. Another SCADA function will use this information.
	#
	# Rolando Urrea. 2019-09-02.
	# v1.1.0: 2025-06-05: added the validation for concentrate expiration.
	# v1.0.1: 2019-02-10: added capability for more than 1 Prebatch system capturing simultaneously.
	# v1.0.0: 2018-09-02.

	import re
	from datetime import datetime
	database = 'Process'

	result = u''
	# Remove the parentheses.
	cleanCode = re.sub('[()* ]', '', barcode)
	# Read specific information.
	lengthIsRight = False
	isComplete = False
	exists = False
	isUnique = False
	isCompatible = False
	isExpired = False
	alreadyCaptured = False
	# Evaluate code size.
	if (len(cleanCode) == 36) or (len(cleanCode) == 38):
		lengthIsRight = True
	result += 'Evaluando: ' + cleanCode + '\n'
	# Check for data to be complete.
	if (lengthIsRight):
		hostname = system.tag.read('[System]Client/Network/Hostname').value
		username = system.tag.read('[System]Client/User/Username').value
		presentationId = cleanCode[3:10]
		presentationBatch = int(cleanCode[12:22])
		# Some codes have full-length year.	
		if (len(cleanCode) == 36):
			presentationExpiration = cleanCode[24:30]
		elif (len(cleanCode) == 38):
			presentationExpiration = cleanCode[26:32]
		expirationEvaluation = presentationExpiration + " 12:00:00"
		dateFormat = "%y%m%d %H:%M:%S"
		expirationDate = datetime.strptime(expirationEvaluation, dateFormat)
		if expirationDate < datetime.now():
			isExpired = True
		presentationSerial = int(cleanCode[-4:])
		if ((presentationBatch > 0) and (presentationSerial > 0)):
			isComplete = True
	# Determine if this presentation exists.
	if (isComplete):
		table = system.db.runPrepQuery('SELECT * FROM pb_component_presentations_current WHERE presentation_id = ?', [presentationId], database)
		if (len(table) > 0):
			exists = True
			# Check every concentrate for package compatibility.
			isCompatible = True
			tagPath = 'Production/Paragon/Process/recipe/Components/'
			# Field loop.
			for i in range(5):
				# Only for valid components in the package.
				# There should be only one row in the table.
				currentPackageRecipeReference = table[0]['recipe_reference']
				currentPackageComponentId = table[0]['c' + ('%02d' % (i + 1)) + '_id']
				currentPackageComponentName = table[0]['c' + ('%02d' % (i + 1)) + '_name']
				if (currentPackageComponentId != '-'):
					concentrateFound = False
					# Component slot loop.
					for j in range(16):
						currentRecipeComponent = system.tag.read(tagPath + 'c' + ('%02d' % (j + 1)) + '/id').value
						if (currentPackageComponentId == currentRecipeComponent):
							concentrateFound = True
					if not(concentrateFound):
						isCompatible = False
						result += '* Componente [' + currentPackageComponentId + '] ' + currentPackageRecipeReference + ' ' + currentPackageComponentName + ' no compatible *\n'
		# Don't wait for the garbage collector to release the table's used memory.
		del table
	# Evaluate for repeated records.
	if (exists):
		table = system.db.runPrepQuery('SELECT presentation_id FROM pb_inventory_capture WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?', [presentationId, presentationBatch, presentationSerial], database)
		if (len(table) > 0):
			alreadyCaptured = True
			system.tag.write('Production/Paragon/Process/Inventory/currentBarcodeRepeated', True)
		# Don't wait for the garbage collector to release the table's used memory.
		del table
	# Finally, search for the record in the history table.
	if exists and not(alreadyCaptured):
		table = system.db.runPrepQuery('SELECT presentation_id FROM pb_inventory_history WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?', [presentationId, presentationBatch, presentationSerial], database)
		if (len(table) == 0):
			isUnique = True
		# Don't wait for the garbage collector to release the table's used memory.
		del table
	# Add to the inventory pool.
	# Non-compatible packages are also included for visual inspection (the isCompatible flag is not considered for insertion).
	if (isUnique and not isExpired):
		result += 'Código: ' + presentationId + ', Lote: ' + str(presentationBatch) + ', Caducidad: ' + presentationExpiration + ', Consecutivo: ' + str(presentationSerial)
		# Insert into the auxiliary table.
		myQuery = 'INSERT INTO pb_inventory_capture (prebatch, capture_host, capture_user, presentation_id, presentation_batch, presentation_expiration, presentation_serial)'
		myQuery += ' VALUES (?, ?, ?, ?, ?, ?, ?)'
		system.db.runPrepUpdate(myQuery, [1, hostname, username, presentationId, presentationBatch, presentationExpiration, presentationSerial], database)
		# Inform if this package is compatible or not.
		if (isCompatible):
			system.tag.write('Production/Paragon/Process/Inventory/currentBarcodeIsCorrect', True)
		else:
			result += '\nERROR: este paquete no es compatible con la receta seleccionada'
			system.tag.write('Production/Paragon/Process/Inventory/wrongCodesExist', True)
	else:
		if alreadyCaptured:
			result += 'Paquete ya capturado; Código: ' + presentationId + ', Lote: ' + str(presentationBatch) + ', Caducidad: ' + presentationExpiration + ', Consecutivo: ' + str(presentationSerial)
		else:
			reason = ''
			if not(lengthIsRight):
				reason += 'la longitud del código es incorrecta'
			elif not(isComplete):
				reason += 'falta información en la cadena'
			elif not(exists):
				reason += 'no existe la referencia a este paquete en la base de datos'
			elif not(isUnique):
				reason += 'este paquete ya ha sido utilizado previamente'
			elif isExpired:
				reason += 'concentrados caducados'
			result += 'ERROR: ' + reason
			system.tag.write('Production/Paragon/Process/Inventory/wrongCodesExist', True)
	return result