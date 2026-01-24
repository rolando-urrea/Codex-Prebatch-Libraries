# Prebatch Frontend function library v2.0.0 ALPHA.
# To be used on Inductive Automation's Ignition platform.
#
# Rolando Urrea.
# 2026-01-23: initial release.

# CONSTANTS.
# Python 2.7 (Ignition's internal Python version, which does not support variable type forcing (VAR:type = value)).
DATABASE = "Process"

def analyze_barcode(prebatch_path, barcode):
	# Determines the id and string quality from the barcode.
	# Two formats are supported: with or without parentheses.
	# With them, the number of letters must be 44; without, 36.
	# Case A (parentheses) format: (240)1819695(10)0001821150(15)181014(90)0085; (240) productId[char * 7] (10) batch[char * 10] (15) expiration_date[char * 6] (90) serial[char * 4].
	# Case B (no parentheses) format: 240181969510000182115015181014900085; 240 productId[char * 7] 10 batch[char * 10] 15 expiration_date[char * 6] 90 serial[char * 4].
	# This function will return a string for logging purposes. It must add the elements from the barcode to the auxiliary table. Another SCADA function will use this information.

	import re
	from datetime import datetime
	result = u""
	# Remove the parentheses.
	clean_code = re.sub("[()* ]", "", barcode)
	# Read specific information.
	length_is_right = False
	is_complete = False
	exists = False
	is_unique = False
	is_compatible = False
	is_expired = False
	already_captured = False
	# Evaluate the barcode size.
	if (len(clean_code) == 36) or (len(clean_code) == 38):
		length_is_right = True
	result += "Evaluando: " + clean_code + "\n"
	presentation_id = ""
	presentation_batch = ""
	presentation_serial = ""
	presentation_expiration = ""
	hostname = ""
	username = ""
	# Check for data to be complete.
	if length_is_right:
		hostname = system.tag.read("[System]Client/Network/Hostname").value
		username = system.tag.read("[System]Client/User/Username").value
		presentation_id = clean_code[3:10]
		presentation_batch = int(clean_code[12:22])
		# Some codes have full-length year.
		presentation_expiration = ""
		if len(clean_code) == 36:
			presentation_expiration = clean_code[24:30]
		elif len(clean_code) == 38:
			presentation_expiration = clean_code[26:32]
		expiration_evaluation = presentation_expiration + " 12:00:00"
		date_format = "%y%m%d %H:%M:%S"
		expiration_date = datetime.strptime(expiration_evaluation, date_format)
		if expiration_date < datetime.now():
			is_expired = True
		presentation_serial = int(clean_code[-4:])
		if (presentation_batch > 0) and (presentation_serial > 0):
			is_complete = True
	# Determine if this presentation exists.
	if is_complete:
		table = system.db.runPrepQuery("SELECT * FROM pb_component_presentations_current WHERE presentation_id = ?", [presentation_id], DATABASE)
		if len(table) > 0:
			exists = True
			# Check every concentrate for package compatibility.
			is_compatible = True
			tag_path = prebatch_path + "Process/baseRecipe/Components/"
			# Field loop.
			for i in range(1, 5):
				# Only for valid components in the package.
				# There should be only one row in the table.
				current_package_recipe_reference = table[0]["recipe_reference"]
				current_package_component_id = table[0]["c" + ("%02d" % i) + "_id"]
				current_package_component_name = table[0]["c" + ("%02d" % i) + "_name"]
				if current_package_component_id != "-":
					concentrate_found = False
					# Component slot loop.
					for j in range(1, 16):
						current_recipe_component = system.tag.read(tag_path + "c" + ("%02d" % j) + "/id").value
						if current_package_component_id == current_recipe_component:
							concentrate_found = True
					if not concentrate_found:
						is_compatible = False
						result += "* Componente [" + current_package_component_id + "] " + current_package_recipe_reference + " " + current_package_component_name + " no compatible *\n"
		# Don't wait for the garbage collector to release the table's used memory.
		table = None
	# Evaluate for repeated records.
	if exists:
		table = system.db.runPrepQuery("SELECT presentation_id FROM pb_inventory_capture WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?", [presentation_id, presentation_batch, presentation_serial], DATABASE)
		if len(table) > 0:
			already_captured = True
			system.tag.writeBlocking(prebatch_path + "Process/Inventory/currentBarcodeRepeated", True)
		# Don't wait for the garbage collector to release the table's used memory.
		table = None
	# Finally, search for the record in the history table.
	if exists and not already_captured:
		table = system.db.runPrepQuery("SELECT presentation_id FROM pb_inventory_history WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?", [presentation_id, presentation_batch, presentation_serial], DATABASE)
		if len(table) == 0:
			is_unique = True
		# Don't wait for the garbage collector to release the table's used memory.
		table = None
	# Add to the inventory pool.
	# Non-compatible packages are also included for visual inspection (the is_compatible flag is not considered for insertion).
	if is_unique and not is_expired:
		prebatch_number = system.tag.read(prebatch_path + "Process/prebatchNumber").value
		result += "Código: " + presentation_id + ", Lote: " + str(presentation_batch) + ", Caducidad: " + presentation_expiration + ", Consecutivo: " + str(presentation_serial)
		# Insert into the auxiliary table.
		my_query = "INSERT INTO pb_inventory_capture (prebatch, capture_host, capture_user, presentation_id, presentation_batch, presentation_expiration, presentation_serial)"
		my_query += " VALUES (?, ?, ?, ?, ?, ?, ?)"
		system.db.runPrepUpdate(my_query, [prebatch_number, hostname, username, presentation_id, presentation_batch, presentation_expiration, presentation_serial], DATABASE)
		# Inform if this package is compatible or not.
		if is_compatible:
			system.tag.writeBlocking(prebatch_path + "Process/Inventory/currentBarcodeIsCorrect", True)
		else:
			result += "\nERROR: este paquete no es compatible con la receta seleccionada"
			system.tag.writeBlocking(prebatch_path + "Process/Inventory/wrongCodesExist", True)
	else:
		if already_captured:
			result += "Paquete ya capturado; Código: " + presentation_id + ", Lote: " + str(presentation_batch) + ", Caducidad: " + presentation_expiration + ", Consecutivo: " + str(presentation_serial)
		else:
			reason = ""
			if not(length_is_right):
				reason += "la longitud del código es incorrecta"
			elif not(is_complete):
				reason += "falta información en la cadena"
			elif not(exists):
				reason += "no existe la referencia a este paquete en la base de datos"
			elif not(is_unique):
				reason += "este paquete ya ha sido utilizado previamente"
			elif is_expired:
				reason += "concentrados caducados"
			result += "ERROR: " + reason
			system.tag.writeBlocking(prebatch_path + "/Process/Inventory/wrongCodesExist", True)
	return result