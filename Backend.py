# Prebatch Backend function library v2.0.0 BETA.
# To be used on Inductive Automation's Ignition platform.
#
# Rolando Urrea.
# Cobalt Processworks.
# 2025-12-14: initial release.

# CONSTANTS.
# Python 2.7 (Ignition's internal Python version, which does not support variable type forcing (VAR:type = value)).
# General.
LOG_INFO_EVENTS = True
LOGGER_NAME = "CodexPrebatchBackend"
# Software database specifications.
# Valid options: PostgreSQL ("PostgreSQL"), Microsoft SQL Server ("SQL Server").
RDBMS = "SQL Server"
DATABASE = "Process"
# Process setup.
POSITION_SLOTS = 16
PROCESSOR_MANAGED = True
BARCODE_EVALUATION = False
LIMIT_UNIT_SELECTION = False
# Estimation for volume evaluation.
SWEETENER_DENSITY = 1.30
SIMPLE_SYRUP_BRIX = 0.60
FRUCTOSE_SOLIDS = 0.77

def machine_conditions_ready(prebatch_path) -> bool:
	"""
	Checks if all the start base conditions are met.
	:param prebatch_path: Prebatch tag path.
	:return: True if all conditions are met, False otherwise.
	"""
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	# The main condition is there should be only one default unit, assigned to a common tank.
	only_one_default_unit = False
	default_unit_is_common = False
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	default_unit_count = 0
	for unit in units:
		if system.tag.read(str(unit["fullPath"]) + "/capabilities/isDefault").value:
			default_unit_count += 1
			if system.tag.read(str(unit["fullPath"]) + "/capabilities/common").value:
				default_unit_is_common = True
	if default_unit_count == 1:
		only_one_default_unit = True
	# Inform there should be only one default unit.
	if default_unit_count != 1:
		logger.errorf("[%s] machine_conditions_ready() [error]: there should be only one default unit", prebatch_name)
	# The default unit must be of the common type.
	if not default_unit_is_common:
		logger.errorf("[%s] machine_conditions_ready() [error]: the default unit must have the 'common' capability", prebatch_name)
	if not default_unit_is_common or not only_one_default_unit:
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	logger = None
	return default_unit_is_common and only_one_default_unit

def clear_component(component_path):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	system.tag.writeBlocking(component_path + "componentId", "")
	system.tag.writeBlocking(component_path + "componentName", "")
	system.tag.writeBlocking(component_path + "componentVersion", 0)
	system.tag.writeBlocking(component_path + "transferPosition", 0)
	system.tag.writeBlocking(component_path + "type", 0)
	system.tag.writeBlocking(component_path + "mass", 0)
	system.tag.writeBlocking(component_path + "water", 0)
	system.tag.writeBlocking(component_path + "hardDissolving", False)
	system.tag.writeBlocking(component_path + "vacuumPump", False)
	system.tag.writeBlocking(component_path + "bayonet", False)
	system.tag.writeBlocking(component_path + "liquidsTank", False)
	system.tag.writeBlocking(component_path + "IBC", False)
	system.tag.writeBlocking(component_path + "circulate", False)
	system.tag.writeBlocking(component_path + "agitationAutomatic", False)
	system.tag.writeBlocking(component_path + "agitationDuration", 0)
	system.tag.writeBlocking(component_path + "requiresHeating", False)
	system.tag.writeBlocking(component_path + "heatingSetpoint", 0)
	system.tag.writeBlocking(component_path + "noInventoryValidation", False)

def clear_all_components(recipe_path, prebatch_name):
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_components() [start]", prebatch_name)
	# Clear the information for each component.
	for i in range(1, POSITION_SLOTS + 1):
		clear_component(recipe_path + "Components/c" + str("%02d" % i) + "/")
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_components() [end]", prebatch_name)
	logger = None

def clear_full_recipe(recipe_path, prebatch_name):
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_full_recipe() [start]", prebatch_name)
	try:
		# Initialize all the recipe's fields.
		system.tag.writeBlocking(recipe_path + "recipeId", "")
		system.tag.writeBlocking(recipe_path + "recipeName", "")
		system.tag.writeBlocking(recipe_path + "recipeType", 0)
		system.tag.writeBlocking(recipe_path + "recipeVersion", 0)
		system.tag.writeBlocking(recipe_path + "userName", "")
		system.tag.writeBlocking(recipe_path + "updateTime", None)
		system.tag.writeBlocking(recipe_path + "density", 1)
		system.tag.writeBlocking(recipe_path + "brix", 0)
		system.tag.writeBlocking(recipe_path + "mass", 0)
		system.tag.writeBlocking(recipe_path + "volume", 0)
		system.tag.writeBlocking(recipe_path + "sucrose", 0)
		system.tag.writeBlocking(recipe_path + "fructose", 0)
		system.tag.writeBlocking(recipe_path + "water", 0)
		# Clear the components.
		clear_all_components(recipe_path, prebatch_name)
	except:
		logger.errorf("[%s] clear_full_recipe() [error]: %s", prebatch_name, str(sys.exc_info()))
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] clear_full_recipe() [end]", prebatch_name)
		logger = None

def clear_production_recipe(recipe_path, prebatch_name):
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_production_recipe() [start]", prebatch_name)
	try:
		# Production recipes have a lot less information than full recipes.
		# The Execution Plans have all the details about concentrates, so there's no need to perform calculations on the components.
		system.tag.writeBlocking(recipe_path + "recipeType", 0)
		system.tag.writeBlocking(recipe_path + "mass", 0)
		system.tag.writeBlocking(recipe_path + "volume", 0)
		system.tag.writeBlocking(recipe_path + "sucrose", 0)
		system.tag.writeBlocking(recipe_path + "fructose", 0)
		system.tag.writeBlocking(recipe_path + "water", 0)
	except:
		logger.errorf("[%s] clear_production_recipe() [error]: %s", prebatch_name, str(sys.exc_info()))
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] clear_production_recipe() [end]", prebatch_name)
		logger = None

def copy_production_recipe(prebatch_name, source_recipe_path, target_recipe_path):
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] copy_production_recipe() [start]", prebatch_name)
	try:
		# Production recipes have a lot less information than full recipes.
		# The Execution Plans have all the details about concentrates, so there's no need to perform calculations on the components.
		# Load data from the source recipe (doing so is easier to understan).
		recipe_type = system.tag.read(source_recipe_path + "recipeType").value
		mass = system.tag.read(source_recipe_path + "mass").value
		volume = system.tag.read(source_recipe_path + "volume").value
		sucrose = system.tag.read(source_recipe_path + "sucrose").value
		fructose = system.tag.read(source_recipe_path + "fructose").value
		water = system.tag.read(source_recipe_path + "water").value
		# Transfer the data to the target recipe.
		system.tag.writeBlocking(target_recipe_path + "recipeType", recipe_type)
		system.tag.writeBlocking(target_recipe_path + "mass", mass)
		system.tag.writeBlocking(target_recipe_path + "volume", volume)
		system.tag.writeBlocking(target_recipe_path + "sucrose", sucrose)
		system.tag.writeBlocking(target_recipe_path + "fructose", fructose)
		system.tag.writeBlocking(target_recipe_path + "water", water)
	except:
		logger.errorf("[%s] copy_production_recipe() [error]: %s", prebatch_name, str(sys.exc_info()))
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] copy_production_recipe() [end]", prebatch_name)
		logger = None

def clear_all_recipes(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_all_recipes() [start]", prebatch_name)
	# Base (full) recipes.
	recipes = ["baseRecipe"]
	for recipe in recipes:
		recipe_path = prebatch_path + "Process/" + recipe + "/"
		if LOG_INFO_EVENTS:
			logger.infof("[%s] clear_all_recipes() [do]: target: %s", prebatch_name, recipe_path)
		clear_full_recipe(recipe_path, prebatch_name)
	# Production (partial) recipes.
	recipes = ["productionRecipe"]
	for recipe in recipes:
		recipe_path = prebatch_path + "Process/" + recipe + "/"
		if LOG_INFO_EVENTS:
			logger.infof("[%s] clear_all_recipes() [do]: target: %s", prebatch_name, recipe_path)
		clear_production_recipe(recipe_path, prebatch_name)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_all_recipes() [end]", prebatch_name)
	logger = None

def load_recipe(prebatch_path, recipe_id):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] load_recipe() [start]: %s", prebatch_name, recipe_id)
	recipe_name = ""
	try:
		recipe_table = system.db.runPrepQuery("SELECT * FROM pb_recipes_current_full WHERE recipe_id = ?", [recipe_id], DATABASE)
		# In case there's no recipe reference in the database, write the error to the logger and clear the recipe.
		if len(recipe_table) == 0:
			logger.errorf("[%s] load_recipe() [do]: recipe %s doesn't exist in the table, there's a problem with the database connection or the RDBMS is not supported (%s)", prebatch_name, recipe_id, RDBMS)
			clear_all_recipes(prebatch_path)
		else:
			# The data should be at row 0.
			# This function only affects the base recipe.
			recipe_path = prebatch_path + "Process/baseRecipe/"
			recipe_data_row = recipe_table[0]
			system.tag.writeBlocking(recipe_path + "recipeId", recipe_data_row["recipe_id"])
			system.tag.writeBlocking(recipe_path + "recipeName", recipe_data_row["recipe_name"])
			recipe_name = recipe_data_row["recipe_name"]
			system.tag.writeBlocking(recipe_path + "recipeType", recipe_data_row["recipe_type"])
			system.tag.writeBlocking(recipe_path + "recipeVersion", recipe_data_row["recipe_version"])
			system.tag.writeBlocking(recipe_path + "userName", recipe_data_row["user_name"])
			system.tag.writeBlocking(recipe_path + "updateTime", recipe_data_row["update_time"])
			system.tag.writeBlocking(recipe_path + "density", recipe_data_row["density"])
			system.tag.writeBlocking(recipe_path + "brix", recipe_data_row["brix"])
			system.tag.writeBlocking(recipe_path + "mass", recipe_data_row["mass"])
			system.tag.writeBlocking(recipe_path + "volume", recipe_data_row["mass"] / recipe_data_row["density"])
			system.tag.writeBlocking(recipe_path + "sucrose", recipe_data_row["sucrose"])
			system.tag.writeBlocking(recipe_path + "fructose", recipe_data_row["fructose"])
			system.tag.writeBlocking(recipe_path + "water", recipe_data_row["water"])
			# Get the information for each component.
			for i in range (1, POSITION_SLOTS + 1):
				component_path = recipe_path + "Components/c" + str("%02d" % i) + "/"
				# Get the component's details.
				component_table = system.db.runPrepQuery("SELECT * FROM pb_components_current WHERE component_id = ?", [recipe_data_row["c" + str("%02d" % i) + "_id"]], DATABASE)
				# In case there's no component reference in the database, initialize its position.
				if len(component_table) == 0:
					clear_component(component_path)
				else:
					component_data_row = component_table[0]
					system.tag.writeBlocking(component_path + "componentId", component_data_row["component_id"])
					system.tag.writeBlocking(component_path + "componentName", component_data_row["component_name"])
					system.tag.writeBlocking(component_path + "componentVersion", component_data_row["component_version"])
					system.tag.writeBlocking(component_path + "transferPosition", [recipe_data_row["c" + str("%02d" % i) + "_pos"]])
					system.tag.writeBlocking(component_path + "type", component_data_row["component_type"])
					system.tag.writeBlocking(component_path + "mass", component_data_row["mass"])
					system.tag.writeBlocking(component_path + "water", component_data_row["water"])
					system.tag.writeBlocking(component_path + "hardDissolving", component_data_row["hard_dissolving"])
					system.tag.writeBlocking(component_path + "vacuumPump", component_data_row["vacuum_pump"])
					system.tag.writeBlocking(component_path + "bayonet", component_data_row["bayonet"])
					system.tag.writeBlocking(component_path + "liquidsTank", component_data_row["liquids_tank"])
					system.tag.writeBlocking(component_path + "IBC", component_data_row["ibc"])
					system.tag.writeBlocking(component_path + "circulate", component_data_row["circulate"])
					system.tag.writeBlocking(component_path + "agitationAutomatic", component_data_row["agitation_duration"] > 0)
					system.tag.writeBlocking(component_path + "agitationDuration", component_data_row["agitation_duration"])
					system.tag.writeBlocking(component_path + "requiresHeating", component_data_row["heating_setpoint"] > 0)
					system.tag.writeBlocking(component_path + "heatingSetpoint", component_data_row["heating_setpoint"])
					system.tag.writeBlocking(component_path + "noInventoryValidation", component_data_row["no_inventory_validation"])
				component_table = None
		recipe_table = None
		system.tag.writeBlocking(prebatch_path + "/Process/loaded", True)
	except:
		logger.errorf("[%s] load_recipe() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] load_recipe() [end]: %s (%s)", prebatch_name, recipe_id, recipe_name)
		logger = None

def clear_execution_position(position_path):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	system.tag.writeBlocking(position_path + "agitationAutomatic", False)
	system.tag.writeBlocking(position_path + "agitationDuration", 0)
	system.tag.writeBlocking(position_path + "bayonet", False)
	system.tag.writeBlocking(position_path + "components", "")
	system.tag.writeBlocking(position_path + "currentCycle", 0)
	system.tag.writeBlocking(position_path + "cycles", 0)
	system.tag.writeBlocking(position_path + "hardDissolving", False)
	system.tag.writeBlocking(position_path + "heatingSetpoint", 0)
	system.tag.writeBlocking(position_path + "liquidsTank", False)
	system.tag.writeBlocking(position_path + "mass", 0)
	system.tag.writeBlocking(position_path + "processUnit", "")
	system.tag.writeBlocking(position_path + "requiresHeating", False)
	system.tag.writeBlocking(position_path + "solidsVacuum", False)
	system.tag.writeBlocking(position_path + "transferPosition", 0)
	system.tag.writeBlocking(position_path + "type", 0)
	system.tag.writeBlocking(position_path + "water", 0)

def clear_all_execution_plans(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	executions_plans = ["baseExecutionPlan", "productionExecutionPlan", "OPCProductionExecutionPlan"]
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_execution_plans() [start]", prebatch_name)
	for execution_plan in executions_plans:
		execution_plan_path = prebatch_path + "Process/" + execution_plan + "/"
		if LOG_INFO_EVENTS:
			logger.infof("[%s] clear_execution_plans() [do]: target: %s", prebatch_name, execution_plan_path)
		for i in range (1, POSITION_SLOTS + 1):
			clear_execution_position(execution_plan_path + "/Positions/p" + str("%02d" % i) + "/")
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_execution_plans() [end]", prebatch_name)
	logger = None

def copy_execution_position(source_position_path, target_position_path, cycles):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	system.tag.writeBlocking(target_position_path + "agitationAutomatic", system.tag.read(source_position_path + "agitationAutomatic").value)
	system.tag.writeBlocking(target_position_path + "agitationDuration", system.tag.read(source_position_path + "agitationDuration").value)
	system.tag.writeBlocking(target_position_path + "bayonet", system.tag.read(source_position_path + "bayonet").value)
	system.tag.writeBlocking(target_position_path + "components", system.tag.read(source_position_path + "components").value)
	system.tag.writeBlocking(target_position_path + "hardDissolving", system.tag.read(source_position_path + "hardDissolving").value)
	system.tag.writeBlocking(target_position_path + "heatingSetpoint", system.tag.read(source_position_path + "heatingSetpoint").value)
	system.tag.writeBlocking(target_position_path + "liquidsTank", system.tag.read(source_position_path + "liquidsTank").value)
	system.tag.writeBlocking(target_position_path + "mass", system.tag.read(source_position_path + "mass").value)
	system.tag.writeBlocking(target_position_path + "processUnit", system.tag.read(source_position_path + "processUnit").value)
	system.tag.writeBlocking(target_position_path + "requiresHeating", system.tag.read(source_position_path + "requiresHeating").value)
	system.tag.writeBlocking(target_position_path + "solidsVacuum", system.tag.read(source_position_path + "solidsVacuum").value)
	system.tag.writeBlocking(target_position_path + "transferPosition", system.tag.read(source_position_path + "transferPosition").value)
	system.tag.writeBlocking(target_position_path + "type", system.tag.read(source_position_path + "type").value)
	system.tag.writeBlocking(target_position_path + "water", system.tag.read(source_position_path + "water").value)
	system.tag.writeBlocking(target_position_path + "cycles", cycles)

def copy_execution_plan(prebatch_path, source_execution_plan_path, target_execution_plan_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] copy_execution_plan(source: %s, target: %s) [start]", prebatch_name, source_execution_plan_path, target_execution_plan_path)
	for i in range(1, POSITION_SLOTS + 1):
		# Define the current positions' paths.
		current_execution_position_path = source_execution_plan_path + "Positions/p" + ("%02d" % i) + "/"
		current_target_execution_plan_path = target_execution_plan_path + "Positions/p" + ("%02d" % i) + "/"
		# Evaluate the process unit.
		process_unit = system.tag.read(current_execution_position_path + "processUnit").value
		# Empty slots will have the Process Unit tag equal to "".
		if process_unit != "":
			position_cycles = system.tag.read(current_execution_position_path + "cycles").value
			copy_execution_position(current_execution_position_path, current_target_execution_plan_path, position_cycles)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] copy_execution_plan(source: %s, target: %s) [end]", prebatch_name, source_execution_plan_path, target_execution_plan_path)
	logger = None

def get_default_unit(prebatch_path):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	return_value = ""
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	for unit in units:
		if system.tag.read(str(unit["fullPath"]) + "/capabilities/isDefault").value:
			return_value = system.tag.read(str(unit["fullPath"]) + "/name").value
	return return_value

def get_unit_from_capability(prebatch_path, capability):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	# Don't consider this function in the logger's scope; it would produce too much detail.
	# If there's no unit with this capability, return the default unit.
	return_value = ""
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	for unit in units:
		if system.tag.read(str(unit["fullPath"]) + "/capabilities/" + capability).value:
			return_value = system.tag.read(str(unit["fullPath"]) + "/name").value
	if return_value == "":
		return_value = get_default_unit(prebatch_path)
		if LOG_INFO_EVENTS:
			logger = system.util.getLogger(LOGGER_NAME)
			logger.infof("[%s] get_unit_from_capability() [do]: no unit with the capability %s found; the default unit was assigned (%s)", prebatch_name, capability, return_value)
			logger = None
	return return_value

def set_base_execution_plan(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	# The Base Execution Plan is performed only for unit limit evaluation.
	# The Production Execution Plan will do water estimation calculations and component partitioning.
	# Hard dissolving tank, suction pump tank, heating tank, liquids tank and bayonet liquid concentrates will remain in their assigned units.
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		recipe_name = system.tag.read(prebatch_path + "Process/baseRecipe/recipeName").value
		logger.infof("[%s] set_base_execution_plan() for %s [start]", prebatch_name, recipe_name)
	try:
		# Start evaluating and accumulating components.
		# Mark position number 1 (the loop won't do this).
		current_position = 1
		components = ""
		mass = 0
		water = 0
		first_item = True
		base_execution_plan_path = prebatch_path + "Process/baseExecutionPlan/"
		system.tag.write(base_execution_plan_path + "Positions/p01/transferPosition", current_position)
		for i in range(1, POSITION_SLOTS + 1):
			# The component path refers to that of the recipe. Hence, the component is individual and the position can contain more than one component.
			component_path = prebatch_path + "Process/baseRecipe/Components/c" + str("%02d" % i) + "/"
			# The position path refers to that of the base execution plan.
			position_path = base_execution_plan_path + "Positions/p" + str("%02d" % current_position) + "/"
			read_position = system.tag.read(component_path + "transferPosition").value
			if read_position > 0:
				# Define if this is the first item in the position.
				if current_position != read_position:
					current_position = read_position
					# Update the current position path.
					position_path = base_execution_plan_path + "Positions/p" + str("%02d" % current_position) + "/"
					# Write the new position number to the transfer position tag.
					system.tag.writeBlocking(position_path + "transferPosition", current_position)
					first_item = True
				# In a multi-concentrate position, give preference to the automatic agitation flag.
				if system.tag.read(component_path + "agitationAutomatic").value:
					agitation_mode = system.tag.read(component_path + "agitationAutomatic").value
					system.tag.writeBlocking(position_path + "agitationAutomatic", agitation_mode)
				# Take the higher agitation duration.
				agitation_duration_position = system.tag.read(position_path + "agitationDuration").value
				agitation_duration_component = system.tag.read(component_path + "agitationDuration").value
				if agitation_duration_position < agitation_duration_component:
					system.tag.writeBlocking(position_path + "agitationDuration", agitation_duration_component)
				# Concatenate the component's name and set a base unit (consider the concentrate has basic requirements).
				# Get the default unit.
				process_unit = get_default_unit(prebatch_path)
				# Get the component type.
				component_type = system.tag.read(component_path + "type").value
				if first_item:
					components = system.tag.read(component_path + "componentName").value
					mass = system.tag.read(component_path + "mass").value
					water = system.tag.read(component_path + "water").value
					# Assign the concentrate type from the first component in this position.
					system.tag.writeBlocking(position_path + "type", component_type)
				else:
					components += ", " + system.tag.read(component_path + "componentName").value
					mass += system.tag.read(component_path + "mass").value
					water += system.tag.read(component_path + "water").value
					# Check if the prior component is different from the current one.
					# If so, assign the common unit to the position.
					assigned_component_type = system.tag.read(position_path + "type").value
					if assigned_component_type != component_type:
						system.tag.writeBlocking(position_path + "type", 3)
						process_unit = get_unit_from_capability(prebatch_path, "common")
				# Set the new value for the component's property and the accumulated data.
				system.tag.writeBlocking(position_path + "components", components)
				system.tag.writeBlocking(position_path + "mass", mass)
				# Water is calculated as is specified in the recipe; however, units that only process liquids should take
				# this value from the rinse volume instead. This is performed in the set_unit_limits() and calculate() function.
				system.tag.writeBlocking(position_path + "water", water)
				# Hard dissolving solid.
				if system.tag.read(component_path + "hardDissolving").value:
					system.tag.writeBlocking(position_path + "hardDissolving", True)
					process_unit = get_unit_from_capability(prebatch_path, "hardDissolving")
				# Vacuum pump.
				if system.tag.read(component_path + "vacuumPump").value:
					system.tag.writeBlocking(position_path + "vacuumPump", True)
					process_unit = get_unit_from_capability(prebatch_path, "vacuumPump")
				# IBC.
				if system.tag.read(component_path + "IBC").value:
					system.tag.writeBlocking(position_path + "IBC", True)
					process_unit = get_unit_from_capability(prebatch_path, "IBC")
				# Liquids tank.
				if system.tag.read(component_path + "liquidsTank").value:
					system.tag.writeBlocking(position_path + "liquidsTank", True)
					process_unit = get_unit_from_capability(prebatch_path, "liquidsTank")
				# Bayonet.
				if system.tag.read(component_path + "bayonet").value:
					system.tag.writeBlocking(position_path + "bayonet", True)
					process_unit = get_unit_from_capability(prebatch_path, "bayonet")
				# Heating.
				if system.tag.read(component_path + "requiresHeating").value:
					system.tag.writeBlocking(position_path + "requiresHeating", True)
					process_unit = get_unit_from_capability(prebatch_path, "requiresHeating")
				# Finally, assign the process unit to the position.
				if first_item:
					system.tag.writeBlocking(position_path + "processUnit", process_unit)
				first_item = False
	except:
		logger.errorf("[%s] set_base_execution_plan() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			recipe_name = system.tag.read(prebatch_path + "Process/baseRecipe/recipeName").value
			logger.infof("[%s] set_base_execution_plan() for %s [end]", prebatch_name, recipe_name)
		logger = None

def set_unit_limit(prebatch_path, tank_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	# Define the unit limit for this recipe/tank combination.
	logger = system.util.getLogger(LOGGER_NAME)
	recipe_name = system.tag.read(prebatch_path + "Process/baseRecipe/recipeName").value
	if LOG_INFO_EVENTS:
		logger.infof("[%s] set_unit_limit() for %s [start]", prebatch_name, recipe_name)
	try:
		recipe_path = prebatch_path + "Process/baseRecipe/"
		recipe_volume = system.tag.read(recipe_path + "volume").value
		# Get the tank's properties.
		tank = system.tag.read(prebatch_path + "Process/tank").value
		tank_min_volume = system.tag.read(tank_path + "Par/minAgitationVolume").value
		tank_max_volume = system.tag.read(tank_path + "Par/capacity").value
		if LOG_INFO_EVENTS:
			logger.infof("[%s] set_unit_limit() [do]: tank: %d, tank_min_volume: %.2f L, tank_max_volume: %.2f L", prebatch_name, tank, tank_min_volume, tank_max_volume)
		max_units = 1
		if recipe_volume > 0:
			max_units = int(tank_max_volume / recipe_volume)
		test_units = max_units
		if LOG_INFO_EVENTS:
			logger.infof("[%s] set_unit_limit() [do]: max_units: %d, volume: %.2f L", prebatch_name, max_units, recipe_volume * max_units)
		recipe_water = 1.0
		required_water = 0.0
		while (recipe_water > required_water) and (test_units > 0):
			test_units -= 1
			dry_base_sucrose = system.tag.read(recipe_path + "sucrose").value
			wet_base_simple_syrup = dry_base_sucrose / SIMPLE_SYRUP_BRIX
			simple_syrup_water = wet_base_simple_syrup - dry_base_sucrose
			dry_base_fructose = system.tag.read(recipe_path + "fructose").value
			wet_base_fructose = dry_base_fructose / FRUCTOSE_SOLIDS
			fructose_water = wet_base_fructose - dry_base_fructose
			sweetener_volume = ((wet_base_simple_syrup + wet_base_fructose) * test_units) / SWEETENER_DENSITY
			sweetener_water = simple_syrup_water + fructose_water
			tank_agitation_water = 0.0
			if sweetener_volume < tank_min_volume:
				tank_agitation_water = tank_min_volume - sweetener_volume
			prebatch_water = 0
			for i in range(1, POSITION_SLOTS + 1):
				current_base_position_path = prebatch_path + "Process/baseExecutionPlan/Positions/p" + ("%02d" % i) + "/"
				process_unit = system.tag.read(current_base_position_path + "processUnit").value
				calculated_water = 0
				# Empty slots will have the Process Unit tag equal to "".
				if process_unit != "":
					calculated_water = system.tag.read(current_base_position_path + "water").value * test_units
					conc_type = system.tag.read(current_base_position_path + "type").value
					pu_par_path = prebatch_path + "Units/" + process_unit + "/Par/"
					pu_min_water_volume = 0
					if conc_type == 1 or conc_type == 3:
						# SOLIDS AND MIXED CONCENTRATES.
						# Prevent a wrong unit configuration for a solid concentrate (the minAgitationVolume tag must exist in the right unit).
						unit_min_agitation_volume = system.tag.read(pu_par_path + "minAgitationVolume").value
						if unit_min_agitation_volume is not None:
							pu_min_water_volume = unit_min_agitation_volume
							# Compare the calculated water volume with the minimum agitation volume required for the unit.
							if pu_min_water_volume < calculated_water:
								pu_min_water_volume = calculated_water
						calculated_water = pu_min_water_volume + system.tag.read(pu_par_path + "rinseVolume").value
					else:
						# LIQUIDS.
						rinse_volume = system.tag.read(pu_par_path + "rinseVolume").value
						pu_cap_path = prebatch_path + "Units/" + process_unit + "/capabilities/"
						is_bayonet = system.tag.read(pu_cap_path + "bayonet").value
						is_ibc = system.tag.read(pu_cap_path + "IBC").value
						is_liquids_tank = system.tag.read(pu_cap_path + "liquidsTank").value
						if is_bayonet or is_ibc or is_liquids_tank:
							# Only consider the rinse volume.
							calculated_water = rinse_volume
						else:
							# Liquids that are poured into the common tank must consider the initial water load.
							calculated_water += rinse_volume
				prebatch_water += calculated_water
			recipe_water = system.tag.read(recipe_path + "water").value * test_units
			required_water = tank_agitation_water + sweetener_water + prebatch_water
		min_units = 1
		if test_units < max_units:
			min_units = test_units + 1
		if min_units < 1:
			min_units = 1
		logger.infof("[%s] set_unit_limit() [do]: min_units: %d, volume: %.2f L", prebatch_name, min_units, recipe_volume * min_units)
		system.tag.writeBlocking(prebatch_path + "Process/userUnits.EngLow", min_units)
		system.tag.writeBlocking(prebatch_path + "Process/userUnits.EngHigh", max_units)
		if LIMIT_UNIT_SELECTION:
			# Set the Engineering Limit Mode to Clamp_Both (3).
			system.tag.writeBlocking(prebatch_path + "Process/userUnits.EngLimitMode", 3)
			system.tag.writeBlocking(prebatch_path + "Process/userUnits", min_units)
		else:
			# Set the Engineering Limit Mode to No_Clamp (0).
			system.tag.writeBlocking(prebatch_path + "Process/userUnits.EngLimitMode", 0)
	except:
		logger.errorf("[%s] set_unit_limit() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] set_unit_limit() for %s [end]", prebatch_name, recipe_name)
		logger = None

def calculate(prebatch_path, tank_path, units):
	import math
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] calculate() [start]", prebatch_name)
	try:
		base_recipe_path = prebatch_path + "Process/baseRecipe/"
		production_recipe_path = prebatch_path + "Process/productionRecipe/"
		recipe_id = system.tag.read(base_recipe_path + "recipeId").value
		recipe_name = system.tag.read(base_recipe_path + "recipeName").value
		# Get the tank's properties.
		tank_min_volume = system.tag.read(tank_path + "Par/minAgitationVolume").value
		if LOG_INFO_EVENTS:
			logger.infof("[%s] calculate() [do]: recipe_id: %s, recipe_name: %s, units: %d", prebatch_name, recipe_id, recipe_name, units)
		# Update the production recipe.
		system.tag.writeBlocking(production_recipe_path + "recipeType", system.tag.read(base_recipe_path + "recipeType").value)
		system.tag.writeBlocking(production_recipe_path + "mass", system.tag.read(base_recipe_path + "mass").value * units)
		system.tag.writeBlocking(production_recipe_path + "volume", system.tag.read(base_recipe_path + "volume").value * units)
		system.tag.writeBlocking(production_recipe_path + "water", system.tag.read(base_recipe_path + "water").value * units)
		system.tag.writeBlocking(production_recipe_path + "sucrose", system.tag.read(base_recipe_path + "sucrose").value * units)
		system.tag.writeBlocking(production_recipe_path + "fructose", system.tag.read(base_recipe_path + "fructose").value * units)
		# Get the dry-base sweeteners and calculate their estimated volume.
		base_sucrose = system.tag.read(base_recipe_path + "sucrose").value
		base_fructose = system.tag.read(base_recipe_path + "fructose").value
		sweetener_volume = ((base_sucrose + base_fructose) * units) / SWEETENER_DENSITY
		# Load the actual content of the tank
		tank_object_name = system.tag.read(tank_path + "name").value
		tank_water_accum = 0
		if tank_object_name is not None:
			tank_water_accum = system.tag.read(tank_path + "Accum/water").value
		# Calculate the additional amount of water required to agitate the tank before adding concentrate.
		tank_agitation_water = 0
		if (sweetener_volume + tank_water_accum) < tank_min_volume:
			tank_agitation_water = tank_min_volume - sweetener_volume - tank_water_accum
		system.tag.writeBlocking(prebatch_path + "Process/tankAgitationWater", tank_agitation_water)
		# Process concentrate.
		current_execution_plan_position = 0
		for i in range(1, POSITION_SLOTS + 1):
			# Define the current positions' paths.
			current_base_position_path = prebatch_path + "Process/baseExecutionPlan/Positions/p" + ("%02d" % i) + "/"
			current_production_position_path = prebatch_path + "Process/productionExecutionPlan/Positions/p" + ("%02d" % i) + "/"
			# Load evaluation data.
			process_unit = system.tag.read(current_base_position_path + "processUnit").value
			# Empty slots will have the Process Unit tag equal to "".
			if process_unit != "":
				copy_execution_position(current_base_position_path, current_production_position_path, 1)
				calculated_mass = system.tag.read(current_base_position_path + "mass").value * units
				system.tag.writeBlocking(current_production_position_path + "mass", calculated_mass)
				# Ensure the water volume is enough for agitation.
				# Liquids will always take the calculated water volume.
				calculated_water = system.tag.read(current_base_position_path + "water").value * units
				pu_min_water_volume = 0
				components = system.tag.read(current_base_position_path + "components").value
				conc_type = system.tag.read(current_base_position_path + "type").value
				pu_par_path = prebatch_path + "Units/" + process_unit + "/Par/"
				cycles = 1
				if conc_type == 1 or conc_type == 3:
					# SOLIDS AND MIXED CONCENTRATES.
					# Prevent a wrong unit configuration for a solid or mixed concentrate (the minAgitationVolume tag must exist in the right unit).
					pu_min_agitation_volume = system.tag.read(pu_par_path + "minAgitationVolume").value
					if pu_min_agitation_volume is not None:
						pu_min_water_volume = pu_min_agitation_volume
					# Compare the calculated water volume with the minimum agitation volume required for the unit.
					if pu_min_water_volume > calculated_water:
						calculated_water = pu_min_water_volume
					# Calculate the required cycles.
					pu_capacity = system.tag.read(pu_par_path + "capacity").value
					calculated_volume = (calculated_water + calculated_mass)
					if pu_capacity is not None:
						if pu_capacity > 0:
							cycles = math.ceil(calculated_volume / pu_capacity)
					if cycles == 0:
						cycles = 1
					system.tag.writeBlocking(current_production_position_path + "water", calculated_water / cycles)
					system.tag.writeBlocking(current_production_position_path + "cycles", cycles)
				else:
					# LIQUIDS.
					# Liquids that are not poured into the common tank must be treated differently.
					rinse_volume = system.tag.read(pu_par_path + "rinseVolume").value
					pu_cap_path = prebatch_path + "Units/" + process_unit + "/capabilities/"
					is_bayonet = system.tag.read(pu_cap_path + "bayonet").value
					is_ibc = system.tag.read(pu_cap_path + "IBC").value
					is_liquids_tank = system.tag.read(pu_cap_path + "liquidsTank").value
					if is_bayonet or is_ibc or is_liquids_tank:
						# Set the water volume is the rinse volume.
						calculated_water = rinse_volume
					# Liquids poured directly into the tank must use the calculated water but with no cycles calculation.
					system.tag.writeBlocking(current_production_position_path + "water", calculated_water)
					system.tag.writeBlocking(current_production_position_path + "cycles", 1)
				if LOG_INFO_EVENTS:
					logger.infof("[%s] calculate() [do]: unit %s found for %s; cycles = %d", prebatch_name, process_unit, components, int(cycles))
				system.tag.writeBlocking(prebatch_path + "Process/maxPosition", i)
		# Set the Calculated Units.
		system.tag.writeBlocking(prebatch_path + "Process/calculatedUnits", units)
	except:
		logger.errorf("[%s] calculate() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] calculate() [end]", prebatch_name)
		logger = None

def save_process_data(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] save_process_data() [start]", prebatch_name)
	last_stored_process_id = None
	recipe_id = ""
	recipe_name = ""
	process_id = 0
	try:
		if RDBMS == "PostgreSQL":
			last_stored_process_id = system.db.runScalarQuery("SELECT process_id FROM pb_recipes_executed ORDER BY process_id DESC LIMIT 1", DATABASE)
		if RDBMS == "SQL Server":
			last_stored_process_id = system.db.runScalarQuery("SELECT TOP 1 process_id FROM pb_recipes_executed ORDER BY process_id DESC", DATABASE)
		if last_stored_process_id is None:
			last_stored_process_id = 0
		process_id = last_stored_process_id + 1
		prebatch_number = system.tag.read(prebatch_path + "Process/prebatchNumber").value
		recipe_path = prebatch_path + "Process/baseRecipe/"
		recipe_id = system.tag.read(recipe_path + "recipeId").value
		recipe_name = system.tag.read(recipe_path + "recipeName").value
		recipe_version = system.tag.read(recipe_path + "recipeVersion").value
		tank = system.tag.read(prebatch_path + "Process/tank").value
		units = system.tag.read(prebatch_path + "Process/calculatedUnits").value
		user_name = system.tag.read(prebatch_path + "Process/userName").value
		if user_name is None:
			user_name = ""
		update_query = "INSERT INTO pb_recipes_executed (prebatch_number, tank, process_id, recipe_id, recipe_version, units, user_name"
		for i in range(1, POSITION_SLOTS + 1):
			update_query += ", c" + ("%02d" % i) + "_version"
		update_query += ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		system.db.runPrepUpdate(update_query, [prebatch_number, tank, process_id, recipe_id, recipe_version, units, user_name,
											   system.tag.read(recipe_path + "Components/c01/componentVersion").value, system.tag.read(recipe_path + "Components/c02/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c03/componentVersion").value, system.tag.read(recipe_path + "Components/c04/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c05/componentVersion").value, system.tag.read(recipe_path + "Components/c06/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c07/componentVersion").value, system.tag.read(recipe_path + "Components/c08/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c09/componentVersion").value, system.tag.read(recipe_path + "Components/c10/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c11/componentVersion").value, system.tag.read(recipe_path + "Components/c12/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c13/componentVersion").value, system.tag.read(recipe_path + "Components/c14/componentVersion").value,
											   system.tag.read(recipe_path + "Components/c15/componentVersion").value, system.tag.read(recipe_path + "Components/c16/componentVersion").value], DATABASE)
		# Update the tank's online contents.
		# tank_object_name = system.tag.read("Production/Paragon/Process/tankObjectName").value
		# system.tag.write("Production/SyrupRoom/Tanks/" + tank_object_name + "/recipe/recipeId", recipe_id)
		# system.tag.write("Production/SyrupRoom/Tanks/" + tank_object_name + "/density", recipe_density)
		# Indicate the process was stored.
		system.tag.write(prebatch_path + "Process/processId", process_id)
	except:
		logger.errorf("[%s] save_process_data() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] save_process_data() [do]: recipe_id: %s, recipe_name: %s, process_id: %d", prebatch_name, recipe_id, recipe_name, process_id)
			logger.infof("[%s] save_process_data() [end]", prebatch_name)
		logger = None

def step_stored(step, cycle, progress_table):
	result = False
	for row_index in range(len(progress_table)):
		if step == progress_table[row_index]["step"] and cycle == progress_table[row_index]["cycle"]:
			result = True
	return result

def coordinate_solids_unit(prebatch_path, pu_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	process_id = system.tag.read(prebatch_path + "Process/processId").value
	logger = system.util.getLogger(LOGGER_NAME)
	try:
		# Get the component's position.
		transfer_position = system.tag.read(pu_path + "executionPosition/transferPosition").value
		# Prevent any error by evaluating the transfer position.
		if transfer_position > 0:
			pu_name = system.tag.read(pu_path + "name").value
			components = system.tag.read(pu_path + "executionPosition/components").value
			started = system.tag.read(pu_path + "start").value
			water_added = system.tag.read(pu_path + "WaterCycle/complete").value
			concentrate_added = system.tag.read(pu_path + "concentrateAdded").value
			agitated = system.tag.read(pu_path + "Agitation/done").value
			transferred = system.tag.read(pu_path + "transferred").value
			current_cycle = system.tag.read(pu_path + "currentCycle").value
			if current_cycle > 0:
				progress_table = system.db.runPrepQuery("SELECT * FROM pb_recipes_progress WHERE process_id = ? AND transfer_position = ? AND cycle = ?", [process_id, transfer_position, current_cycle], DATABASE)
				# Step 1: sequence started.
				if started and not(step_stored(1, current_cycle, progress_table)):
					system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle) VALUES (?, ?, ?, ?)", [process_id, transfer_position, 1, current_cycle], DATABASE)
					logger.infof("[%s] coordinate_solids_unit [do]: update STARTED status for %s (%s)", prebatch_name, pu_name, components)
				# Step 2: water was added.
				if started and water_added and not(step_stored(2, current_cycle, progress_table)):
					water_accum = system.tag.read(pu_path + "WaterCycle/accum").value
					system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle, water) VALUES (?, ?, ?, ?, ?)", [process_id, transfer_position, 2, current_cycle, water_accum], DATABASE)
					logger.infof("[%s] coordinate_solids_unit [do]: update WATER ADDED status for %s (%s) [%.2f L]", prebatch_name, pu_name, components, water_accum)
				# Step 3: the concentrate was added.
				if started and concentrate_added and not(step_stored(3, current_cycle, progress_table)):
					system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle) VALUES (?, ?, ?, ?)", [process_id, transfer_position, 3, current_cycle], DATABASE)
					logger.infof("[%s] coordinate_solids_unit [do]: update CONCENTRATE ADDED status for %s (%s)", prebatch_name, pu_name, components)
				# Step 4: the agitation concluded.
				if started and agitated and not(step_stored(4, current_cycle, progress_table)):
					system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle) VALUES (?, ?, ?, ?)", [process_id, transfer_position, 4, current_cycle], DATABASE)
					logger.infof("[%s] coordinate_solids_unit [do]: update AGITATION CONCLUDED status for %s (%s)", prebatch_name, pu_name, components)
				# Step 5: the concentrate was transferred.
				if started and transferred and not(step_stored(5, current_cycle, progress_table)):
					rinse_accum = system.tag.read(pu_path + "RinseCycle/accum").value
					system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle, water) VALUES (?, ?, ?, ?, ?)", [process_id, transfer_position, 5, current_cycle, rinse_accum], DATABASE)
					logger.infof("[%s] coordinate_solids_unit [do]: update TRANSFERRED status for %s (%s) [%.2f L]", prebatch_name, pu_name, components, rinse_accum)
	except:
		logger.errorf("[%s] coordinate_solids_unit() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		logger = None

def coordinate_liquids_unit(prebatch_path, pu_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	process_id = system.tag.read(prebatch_path + "Process/processId").value
	logger = system.util.getLogger(LOGGER_NAME)
	try:
		# Get the component's position.
		transfer_position = system.tag.read(pu_path + "executionPosition/transferPosition").value
		# Prevent any error by evaluating the transfer position.
		if transfer_position > 0:
			pu_name = system.tag.read(pu_path + "name").value
			components = system.tag.read(pu_path + "executionPosition/components").value
			started = system.tag.read(pu_path + "start").value
			transferred = system.tag.read(pu_path + "transferred").value
			current_cycle = 1
			# Liquids have no more than one cycle, so there's no need for its validation in the query.
			progress_table = system.db.runPrepQuery("SELECT * FROM pb_recipes_progress WHERE process_id = ? AND transfer_position = ?", [process_id, transfer_position], DATABASE)
			# Step 1: sequence started.
			if started and not(step_stored(1, 1, progress_table)):
				system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle) VALUES (?, ?, ?, ?)", [process_id, transfer_position, 1, current_cycle], DATABASE)
				logger.infof("[%s] coordinate_liquids_unit [do]: update STARTED status for %s (%s)", prebatch_name, pu_name, components)
			# Step 5: the concentrate was transferred.
			if started and transferred and not(step_stored(5, 1, progress_table)):
				rinse_accum = system.tag.read(pu_path + "WaterCycle/accum").value
				system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, transfer_position, step, cycle, water) VALUES (?, ?, ?, ?, ?)", [process_id, transfer_position, 5, current_cycle, rinse_accum], DATABASE)
				logger.infof("[%s] coordinate_liquids_unit [do]: update TRANSFERRED status for %s (%s) [%.2f L]", prebatch_name, pu_name, components, rinse_accum)
	except:
		logger.errorf("[%s] coordinate_liquids_unit() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		logger = None

def coordinate(prebatch_path):
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	for unit in units:
		# The nature of the concentrates requires different handling in the coordination function.
		# The differences between solid concentrates are handled in the HMI application.
		is_bayonet = system.tag.read(str(unit["fullPath"]) + "/capabilities/bayonet").value
		is_ibc = system.tag.read(str(unit["fullPath"]) + "/capabilities/IBC").value
		is_liquids_tank = system.tag.read(str(unit["fullPath"]) + "/capabilities/liquidsTank").value
		if is_bayonet or is_ibc or is_liquids_tank:
			coordinate_liquids_unit(prebatch_path, str(unit["fullPath"]) + "/")
		else:
			coordinate_solids_unit(prebatch_path, str(unit["fullPath"]) + "/")
	if not PROCESSOR_MANAGED:
		# Evaluate if all the positions were processed.
		current_position = system.tag.read(prebatch_path + "Process/currentPosition").value
		max_position = system.tag.read(prebatch_path + "Process/maxPosition").value
		if current_position > max_position:
			system.tag.writeBlocking(prebatch_path + "Process/concentrateTransferred", True)

def initialize_flags(prebatch_path):
	system.tag.writeBlocking(prebatch_path + "Process/start", False)
	system.tag.writeBlocking(prebatch_path + "Process/finalize", False)
	# system.tag.writeBlocking(prebatch_path + "Process/started", False)
	system.tag.writeBlocking(prebatch_path + "Process/abort", False)
	system.tag.writeBlocking(prebatch_path + "Process/reset", False)
	system.tag.writeBlocking(prebatch_path + "Process/userConfirmation", False)
	system.tag.writeBlocking(prebatch_path + "Process/concentrateTransferred", False)
	system.tag.writeBlocking(prebatch_path + "Process/dataTransferred", False)
	system.tag.writeBlocking(prebatch_path + "Process/loaded", False)
	system.tag.writeBlocking(prebatch_path + "Process/processing", False)
	system.tag.writeBlocking(prebatch_path + "Process/processId", 0)
	system.tag.writeBlocking(prebatch_path + "Process/calculatedUnits", 0)
	system.tag.writeBlocking(prebatch_path + "Process/userUnits.EngLow", 0)
	system.tag.writeBlocking(prebatch_path + "Process/userUnits.EngHigh", 100)
	system.tag.writeBlocking(prebatch_path + "Process/userUnits", 0)
	system.tag.writeBlocking(prebatch_path + "Process/currentPosition", 0)
	system.tag.writeBlocking(prebatch_path + "Process/maxPosition", 0)
	system.tag.writeBlocking(prebatch_path + "Process/tank", 0)
	system.tag.writeBlocking(prebatch_path + "Process/tankAgitationWater", 0)
	system.tag.writeBlocking(prebatch_path + "Process/userName", "-")

def initialize_inventory_flags(prebatch_path):
	inventory_path = prebatch_path + "Process/Inventory/"
	system.tag.writeBlocking(inventory_path + "correct", False)
	system.tag.writeBlocking(inventory_path + "currentBarcodeIsCorrect", False)
	system.tag.writeBlocking(inventory_path + "skip", False)
	system.tag.writeBlocking(inventory_path + "wrongCodesExist", False)

def module_available(prebatch_path, transfer_position):
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	result = True
	for unit in units:
		if system.tag.read(str(unit["fullPath"]) + "/positionObject/transferPosition").value == transfer_position:
			result = False
	return result

def check_inventory_completion(prebatch_path):
	logger = system.util.getLogger(LOGGER_NAME)
	try:
		# Check if barcode validation is active.
		if system.tag.read(prebatch_path + "Process/Inventory/skip").value:
			system.tag.writeBlocking(prebatch_path + "Process/Inventory/correct", True)
		else:
			current_correct_flag = system.tag.read(prebatch_path + "Process/Inventory/correct").value
			result = False
			if not system.tag.read(prebatch_path + "Process/Inventory/wrongCodesExist").value:
				result = True
				required_units = system.tag.read(prebatch_path + "/Process/calculatedUnits").value
				prebatch_number = system.tag.read(prebatch_path + "/Process/prebatchNumber").value
				table = system.db.runPrepQuery("SELECT * FROM pb_inventory_capture_detailed WHERE prebatch = ?", [prebatch_number], DATABASE)
				if len(table) > 0:
					tag_path = prebatch_path + "Process/baseRecipe/Components/"
					# Component slot loop.
					for i in range(1, POSITION_SLOTS + 1):
						# Each required concentrate has to be checked in the capture table.
						# The loop has to compare its existence and the unit amount.
						# Since there can be different component presentations in the same production recipe, accumulation has to be performed.
						concentrate_found = False
						current_recipe_component = system.tag.read(tag_path + "c" + ("%02d" % i) + "/componentId").value
						requires_inventory_validation = not system.tag.read(tag_path + "c" + ("%02d" % i) + "/noInventoryValidation").value
						if (current_recipe_component != "") and requires_inventory_validation:
							component_units = 0
							for row_index in range(len(table)):
								# Field loop.
								for j in range(1, 6):
									current_package_component_id = table[row_index]["c" + ("%02d" % j) + "_id"]
									if current_package_component_id == current_recipe_component:
										component_units += table[row_index]["units_total"]
							if required_units == component_units:
								concentrate_found = True
						else:
							concentrate_found = True
						if not concentrate_found:
							result = False
				else:
					result = False
				# Don't wait for the garbage collector to release the table's used memory.
				table = None
			system.tag.write(prebatch_path + "/Process/Inventory/correct", result)
			# Send a message to the logger only if there's a change in the correct flag.
			if current_correct_flag != result:
				if LOG_INFO_EVENTS:
					prebatch_name = system.tag.read(prebatch_path + "/Process/prebatchName").value
					logger.infof("[%s] check_inventory_completion() [do]: correct: %s", prebatch_name, result)
				system.tag.writeBlocking(prebatch_path + "Process/Inventory/correct", result)
	except:
		prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
		logger.errorf("[%s] check_inventory_completion() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		logger = None

def save_inventory(prebatch_path):
	logger = system.util.getLogger(LOGGER_NAME)
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	prebatch_number = system.tag.read(prebatch_path + "Process/prebatchNumber").value
	if LOG_INFO_EVENTS:
		logger.infof("[%s] save_inventory() [start]", prebatch_name)
	try:
		# Transfers the records from the capture table to the history one.
		process_id = system.tag.read(prebatch_path + "Process/processId").value
		capture_table = system.db.runPrepQuery("SELECT * FROM pb_inventory_capture WHERE prebatch = ?", [prebatch_number], DATABASE)
		tx_id = system.db.beginTransaction(DATABASE, timeout=5000)
		for row_index in range(len(capture_table)):
			local_row = capture_table[row_index]
			# Update history.
			update_query = "INSERT INTO pb_inventory_history (process_id, capture_host, capture_user, presentation_id, presentation_batch, presentation_expiration, presentation_serial, update_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
			system.db.runPrepUpdate(update_query, [process_id, local_row["capture_host"], local_row["capture_user"], local_row["presentation_id"], local_row["presentation_batch"], local_row["presentation_expiration"], local_row["presentation_serial"], local_row["update_time"]], database, tx_id)
			# Update warehouse data.
			if RDBMS == "PostgreSQL":
				update_query = "UPDATE pb_inventory_warehouse SET is_active = FALSE WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?"
			if RDBMS == "SQL Server":
				update_query = "UPDATE pb_inventory_warehouse SET is_active = 0 WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?"
			system.db.runPrepUpdate(update_query, [local_row["presentation_id"], local_row["presentation_batch"], local_row["presentation_serial"]], DATABASE, tx_id)
			update_query = "INSERT INTO pb_inventory_warehouse (presentation_id, presentation_batch, presentation_serial, presentation_expiration) VALUES (?, ?, ?, ?)"
			system.db.runPrepUpdate(update_query, [local_row["presentation_id"], local_row["presentation_batch"], local_row["presentation_serial"], local_row["presentation_expiration"], "Salida por consumo"], DATABASE, tx_id)
		system.db.commitTransaction(tx_id)
		system.db.closeTransaction(tx_id)
		# Don't wait for the garbage collector to release the table's used memory.
		capture_table = None
		system.db.runPrepUpdate("DELETE FROM pb_inventory_capture WHERE prebatch = 1", [], DATABASE)
	except:
		logger.errorf("[%s] save_inventory() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] store_inventory() [end]", prebatch_name)
		logger = None

def cancel_running_recipe(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	process_id = system.tag.read(prebatch_path + "Process/processId").value
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] cancel_running_recipe() [start]", prebatch_name)
	try:
		# Prevent error from a previously inserted canceled recipe id.
		# This could happen when there was a previous exception and this line was reached.
		stored_canceled_recipe_id = system.db.runScalarPrepQuery("SELECT process_id FROM pb_recipes_canceled WHERE process_id = ?", [process_id], DATABASE)
		if stored_canceled_recipe_id is None:
			system.db.runPrepUpdate("INSERT INTO pb_recipes_canceled (process_id) VALUES (?)", [process_id], DATABASE)
	except:
		logger.errorf("[%s] cancel_running_recipe() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] cancel_running_recipe() [end]", prebatch_name)
		logger = None

def save_final_data(prebatch_path):
	logger = system.util.getLogger(LOGGER_NAME)
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	if LOG_INFO_EVENTS:
		logger.infof("[%S] save_final_data() [start]", prebatch_name)
	try:
		process_id = system.tag.read(prebatch_path + "Process/processId").value
		recipe_id = system.tag.read(prebatch_path + "Process/baseRecipe/recipeId").value
		recipe_name = system.tag.read(prebatch_path + "Process/baseRecipe/recipeName").value
		tank = system.tag.read(prebatch_path + "Process/tank").value
		# In the case the process was canceled, there's a chance the tank was set to zero already.
		# If this is the case
		if tank > 0:
			tank_accum_path = "[default]Production/SyrupRoom/Tanks/FinishedSyrup/T" + ("%02d" % tank) + "/Accum/"
			water = system.tag.read(tank_accum_path + "water").value
			sucrose = system.tag.read(tank_accum_path + "sucrose").value
			fructose = system.tag.read(tank_accum_path + "fructose").value
			# Prevent double insertion.
			stored_process_id = system.db.runScalarPrepQuery("SELECT process_id FROM finished_syrup_tanks_data WHERE process_id = ?", [process_id], DATABASE)
			if stored_process_id is None:
				system.db.runPrepUpdate("INSERT INTO finished_syrup_tanks_data (process_id, tank_id, sucrose, fructose, water) VALUES (?, ?, ?, ?, ?)", [process_id, tank, sucrose, fructose, water], DATABASE)
			logger.infof("[%s] save_final_data() [do]: recipeId: %s, recipeName: %s, processId: %d", prebatch_name, recipe_id, recipe_name, process_id)
		else:
			logger.infof("[%s] save_final_data() [do]: recipeId: %s, recipeName: %s, processId: %d; the tank was already initialized (caused by a canceled process)", prebatch_name, recipe_id, recipe_name, process_id)
	except:
		logger.errorf("[%s] save_final_data() [error]: %s", prebatch_name, str(sys.exc_info()))
		system.tag.writeBlocking(prebatch_path + "/Process/backendAlarmed", True)
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] save_final_data() [end]", prebatch_name)
		logger = None

def main(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	# The Reset Alarms button in the HMI should reset the Alarmed flag.
	system_alarmed = system.tag.read(prebatch_path + "Process/backendAlarmed").value
	# Verify there's a correct configuration in the system.
	if not system_alarmed:
		if machine_conditions_ready(prebatch_path):
			# The base point of the evaluation is the Started tag and its quality.
			started_tag = system.tag.read(prebatch_path + "Process/started")
			# First, check the PLC is online.
			if started_tag.quality.isGood:
				started = started_tag.value
				process_id = system.tag.read(prebatch_path + "Process/processId").value
				if started:
					# The process was started, which means all the requirements were met. If there's no process id, assign a new one.
					# Otherwise, keep coordinating the sequences.
					if process_id != 0:
						concentrate_transferred = system.tag.read(prebatch_path + "Process/concentrateTransferred").value
						if not concentrate_transferred:
							coordinate(prebatch_path)
					else:
						system.tag.writeBlocking(prebatch_path + "Process/processing", True)
						if LOG_INFO_EVENTS:
							logger.infof("[%s] main() [do]: %s", prebatch_name, "--- SYSTEM STARTED ---")
						save_process_data(prebatch_path)
						system.tag.writeBlocking(prebatch_path + "Process/processing", False)
				else:
					# The Loaded flag involves that a valid recipe was selected, as well as the target tank.
					loaded = system.tag.read(prebatch_path + "Process/loaded").value
					tank = system.tag.read(prebatch_path + "Process/tank").value
					tank_path = "[default]Production/SyrupRoom/Tanks/FinishedSyrup/T" + ("%02d" % tank) + "/"
					if loaded:
						# The Loaded flag should disable the buttons for recipe and tank selection.
						# If the user needs to change the recipe or tank, the process must be reset.
						calculated_units = system.tag.read(prebatch_path + "Process/calculatedUnits").value
						user_units = system.tag.read(prebatch_path + "Process/userUnits").value
						if calculated_units != user_units or calculated_units == 0:
							system.tag.writeBlocking(prebatch_path + "Process/processing", True)
							calculate(prebatch_path, tank_path, user_units)
							system.tag.writeBlocking(prebatch_path + "Process/processing", False)
						# Check if the calculated units are the same as the user units and they're greater than zero.
						# Also wait for user confirmation.
						if calculated_units == user_units and user_units > 0:
							user_confirmation = system.tag.read(prebatch_path + "Process/userConfirmation").value
							data_transferred = system.tag.read(prebatch_path + "Process/dataTransferred").value
							if user_confirmation and not data_transferred:
								# Transfer the execution plan to the processor and mark set the Transferred flag to True.
								# This will stop cyclic data transfer.
								system.tag.writeBlocking(prebatch_path + "Process/processing", True)
								copy_execution_plan(prebatch_path, prebatch_path + "Process/productionExecutionPlan/",
													prebatch_path + "Process/OPCProductionExecutionPlan/")
								copy_production_recipe(prebatch_name, prebatch_path + "Process/productionRecipe/", prebatch_path + "Process/OPCProductionRecipe/")
								if LOG_INFO_EVENTS:
									logger.infof("[%s] main() [do]: %s", prebatch_name, "--- SYSTEM READY TO START ---")
								system.tag.writeBlocking(prebatch_path + "Process/dataTransferred", True)
								system.tag.writeBlocking(prebatch_path + "Process/processing", False)
						if calculated_units == user_units:
							system.tag.writeBlocking(prebatch_path + "Process/loaded", True)
						# Evaluate inventory completion (if it's available).
						if BARCODE_EVALUATION:
							check_inventory_completion(prebatch_path)
					else:
						recipe_id = system.tag.read(prebatch_path + "Process/baseRecipe/recipeId").value
						if recipe_id is not None:
							# Wait until there's the right selection of the recipe and finished syrup tank.
							if recipe_id != "" and tank > 0:
								system.tag.writeBlocking(prebatch_path + "Process/processing", True)
								load_recipe(prebatch_path, recipe_id)
								set_base_execution_plan(prebatch_path)
								set_unit_limit(prebatch_path, tank_path)
								system.tag.writeBlocking(prebatch_path + "Process/processing", False)
				# The Finalize flag comes from a button in the HMI, indicating that the process was ended successfully.
				# Also, there must be an option for process reset and abort (another set of buttons in the HMI).
				aborted = system.tag.read(prebatch_path + "Process/abort").value
				finalized = system.tag.read(prebatch_path + "Process/finalize").value
				reset = system.tag.read(prebatch_path + "Process/reset").value
				if aborted or finalized or reset:
					system.tag.writeBlocking(prebatch_path + "Process/processing", True)
					# Sometimes a few flags can be on when initializing the system.
					if process_id > 0:
						if aborted:
							cancel_running_recipe(prebatch_path)
						if aborted or finalized:
							if BARCODE_EVALUATION:
								save_inventory(prebatch_path)
							save_final_data(prebatch_path)
					initialize_flags(prebatch_path)
					initialize_inventory_flags(prebatch_path)
					clear_all_recipes(prebatch_path)
					clear_all_execution_plans(prebatch_path)
					if LOG_INFO_EVENTS:
						logger.infof("[%s] main() [do]: %s", prebatch_name, "--- SYSTEM FINISHED ---")
					system.tag.writeBlocking(prebatch_path + "Process/processing", False)
	logger = None

def initialize_module(position):
	logger = system.util.getLogger(LOGGER_NAME)
	logger.infof("[Paragon] initialize_module(position: %d) [start]", position)
	initialization_path = ""
	unit_to_initialize = ""
	# Tank T-01.
	if (system.tag.read("Production/Paragon/Tanks/T01/executionPosition/cition").value == position):
		initialization_path = "Production/Paragon/Tanks/T01/"
		unit_to_initialize = "T-01"
	# Tank T-02.
	if (system.tag.read("Production/Paragon/Tanks/T02/executionPosition/cition").value == position):
		initialization_path = "Production/Paragon/Tanks/T02/"
		unit_to_initialize = "T-02"
	# Bayonet 1.
	if (system.tag.read("Production/Paragon/Tanks/B01/executionPosition/cition").value == position):
		initialization_path = "Production/Paragon/Tanks/B01/"
		unit_to_initialize = "B-01"
	# Perform the initialization.
	logger.infof("[Paragon] initialize_module(position: %d) [do]: initialize unit %s", position, unit_to_initialize)
	system.tag.writeSynchronous(initialization_path + "inTransferPosition", False)
	system.tag.writeSynchronous(initialization_path + "unitControl/abort", True)
	system.tag.writeSynchronous(initialization_path + "unitControl/pause", True)
	# Initialize the unit's position.
	position_path = initialization_path + "executionPosition/"
	system.tag.writeSynchronous(position_path + "position", 0, 5000)
	system.tag.writeSynchronous(position_path + "processUnit", "", 5000)
	system.tag.write(position_path + "agitationAutomatic", False)
	system.tag.write(position_path + "agitationDuration", 0)
	system.tag.write(position_path + "baseMass", 0)
	system.tag.write(position_path + "baseWater", 0)
	system.tag.write(position_path + "bayonet", False)
	system.tag.write(position_path + "calculatedMass", 0)
	system.tag.write(position_path + "calculatedWater", 0)
	system.tag.write(position_path + "changeAllowed", False)
	system.tag.writeSynchronous(position_path + "components", "", 5000)
	system.tag.write(position_path + "type", 0)
	# Initialize the processor's flags.
	system.tag.writeSynchronous(initialization_path + "initializeProcessor", False)
	logger.infof("[Paragon] initialize_module(position: %d, unit %s) [end]", position, unit_to_initialize)
	del logger

def process_component(position, in_transfer_position):
	logger = system.util.getLogger(LOGGER_NAME)
	logger.infof("[Paragon] process_component(position: %d, in_transfer_position: %s) [start]", position, in_transfer_position)
	process_unit = system.tag.read("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/processUnit").value
	# Tank T-01.
	if (process_unit == "T-01"):
		# Copy the position if required.
		if (system.tag.read("Production/Paragon/Tanks/T01/executionPosition/cition").value != position):
			copy_execution_position("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/", "Production/Paragon/Tanks/T01/executionPosition/", 1)
		system.tag.writeSynchronous("Production/Paragon/Tanks/T01/inTransferPosition", in_transfer_position, 5000)
	# Tank T-02.
	if (process_unit == "T-02"):
		# Copy the position if required.
		if (system.tag.read("Production/Paragon/Tanks/T02/executionPosition/cition").value != position):
			copy_execution_position("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/", "Production/Paragon/Tanks/T02/executionPosition/", 1)
		system.tag.writeSynchronous("Production/Paragon/Tanks/T02/inTransferPosition", in_transfer_position, 5000)
	# Bayonet.
	if (process_unit == "B-01"):
		# Copy the position if required.
		if (system.tag.read("Production/Paragon/Tanks/B01/executionPosition/cition").value != position):
			copy_execution_position("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/", "Production/Paragon/Tanks/B01/executionPosition/", 1)
		system.tag.writeSynchronous("Production/Paragon/Tanks/B01/inTransferPosition", in_transfer_position, 5000)
	logger.infof("[Paragon] process_component(position: %d, in_transfer_position: %s) [end]", position, in_transfer_position)
	del logger

def skip_current_component():
	logger = system.util.getLogger(LOGGER_NAME)
	logger.info("[Paragon] skip_current_component [start]")	
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	current_position = system.tag.read("Production/Paragon/Process/currentPosition").value
	database = "Process"
	system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, manual) VALUES (?, ?, ?, ?)", [process_id, current_position, 5, True], database)
	logger.info("[Paragon] skip_current_component [end]")
	del logger