# Prebatch Backend function library v2.0.0 ALPHA.
# To be used on Inductive Automation's Ignition platform.
#
# Rolando Urrea.
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
PROCESSOR_MANAGED = False
# Estimation for volume evaluation.
SWEETENER_DENSITY = 1.30
SIMPLE_SYRUP_BRIX = 0.60
FRUCTOSE_SOLIDS = 0.77

def mark_process_start(prebatch_name, tank_name):
	# This function is used just to mark the start of the process, determined when a tank is selected.
	if LOG_INFO_EVENTS:
		logger = system.util.getLogger(LOGGER_NAME)
		logger.infof("[%s] *** Process START ***", prebatch_name)
		logger.infof("[%s] Target tank: %s", prebatch_name, tank_name)
		logger = None

def mark_process_end(prebatch_name):
	# This function is used just to mark the end of the process.
	if LOG_INFO_EVENTS:
		logger = system.util.getLogger(LOGGER_NAME)
		logger.infof("[%s] *** Process END ***", prebatch_name)
		logger = None

def machine_conditions_ready(prebatch_path, prebatch_name):
	# Checks if all the start base conditions are met.
	# TODO: add external batch management conditions (Prebatch and Tank allocated, as well as the concentrate dosing phases active).
	# TODO: create a memory tag to indicate there's a problem with the machine conditions; this should prevent the logger from creating constant entries if the error persists.
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] start_conditions_ready() [start]", prebatch_name)
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
		logger.errorf("[%s] start_conditions_ready() [error]: there should be only one default unit", prebatch_name)
	# The default unit must be of the common type.
	if not default_unit_is_common:
		logger.errorf("[%s] start_conditions_ready() [error]: the default unit must have the 'common' capability", prebatch_name)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] start_conditions_ready() [end]: %b", prebatch_name, default_unit_is_common and only_one_default_unit)
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
		system.tag.writeBlocking(recipe_path + "recipeId", "-")
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

def clear_all_recipes(prebatch_path, prebatch_name):
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_all_recipes() [start]", prebatch_name)
	# Base (full) recipes.
	recipes = ["baseRecipe"]
	for recipe in recipes:
		recipe_path = prebatch_path + "Process/" + recipe + "/"
		logger.infof("[%s] clear_all_recipes() [do]: target: %s", prebatch_name, recipe_path)
		clear_full_recipe(recipe_path, prebatch_name)
	# Production (partial) recipes.
	recipes = ["productionRecipe"]
	for recipe in recipes:
		recipe_path = prebatch_path + "Process/" + recipe + "/"
		logger.infof("[%s] clear_all_recipes() [do]: target: %s", prebatch_name, recipe_path)
		clear_production_recipe(recipe_path, prebatch_name)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_all_recipes() [end]", prebatch_name)
	logger = None

def load_recipe(prebatch_path, prebatch_name, recipe_id):
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] load_recipe() [start]: %s", prebatch_name, recipe_id)
	recipe_name = ""
	try:
		# This query is the same among the RDBMS systems.
		recipe_table = None
		recipe_table = system.db.runPrepQuery("SELECT * FROM pb_recipes_current_full WHERE recipe_id = ?", [recipe_id], DATABASE)
		# In case there's no recipe reference in the database, write the error to the logger and clear the recipe.
		if len(recipe_table) == 0:
			logger.errorf("[%s] load_recipe() [do]: recipe %s doesn't exist in the table, there's a problem with the database connection or the RDBMS is not supported (%s)", prebatch_name, recipe_id, RDBMS)
			clear_all_recipes(prebatch_path, prebatch_name)
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
				# This query is the same among the RDBMS systems.
				component_table = None
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
		recipe_table= None
	except:
		logger.errorf("[%s] load_recipe() [error]: %s", prebatch_name, str(sys.exc_info()))
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

def clear_all_execution_plans(prebatch_path, prebatch_name):
	executions_plans = ["baseExecutionPlan", "productionExecutionPlan", "productionOPCExecutionPlan"]
	logger = system.util.getLogger(LOGGER_NAME)
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_execution_plans() [start]", prebatch_name)
	for execution_plan in executions_plans:
		execution_plan_path = prebatch_path + "Process/" + execution_plan + "/"
		logger.infof("[%s] clear_execution_plans() [do]: target: %s", prebatch_name, execution_plan_path)
		for i in range (1, POSITION_SLOTS + 1):
			clear_execution_position(execution_plan_path + "/Positions/p" + str("%02d" % i) + "/")
	if LOG_INFO_EVENTS:
		logger.infof("[%s] clear_execution_plans() [end]", prebatch_name)
	logger = None

def copy_position(source_position_path, target_position_path, cycles):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	# Omit the mass and water tags, since those are calculated in other functions.
	system.tag.writeBlocking(target_position_path + "agitationAutomatic", system.tag.read(source_position_path + "agitationAutomatic").value)
	system.tag.writeBlocking(target_position_path + "agitationDuration", system.tag.read(source_position_path + "agitationDuration").value)
	system.tag.writeBlocking(target_position_path + "bayonet", system.tag.read(source_position_path + "bayonet").value)
	system.tag.writeBlocking(target_position_path + "components", system.tag.read(source_position_path + "components").value)
	system.tag.writeBlocking(target_position_path + "hardDissolving", system.tag.read(source_position_path + "hardDissolving").value)
	system.tag.writeBlocking(target_position_path + "heatingSetpoint", system.tag.read(source_position_path + "heatingSetpoint").value)
	system.tag.writeBlocking(target_position_path + "liquidsTank", system.tag.read(source_position_path + "liquidsTank").value)
	# system.tag.writeBlocking(target_position_path + "mass", system.tag.read(source_position_path + "mass").value)
	system.tag.writeBlocking(target_position_path + "processUnit", system.tag.read(source_position_path + "processUnit").value)
	system.tag.writeBlocking(target_position_path + "requiresHeating", system.tag.read(source_position_path + "requiresHeating").value)
	system.tag.writeBlocking(target_position_path + "solidsVacuum", system.tag.read(source_position_path + "solidsVacuum").value)
	system.tag.writeBlocking(target_position_path + "transferPosition", system.tag.read(source_position_path + "transferPosition").value)
	system.tag.writeBlocking(target_position_path + "type", system.tag.read(source_position_path + "type").value)
	# system.tag.writeBlocking(target_position_path + "water", system.tag.read(source_position_path + "water").value)
	system.tag.writeBlocking(target_position_path + "cycles", cycles)

def get_default_unit(prebatch_path, prebatch_name):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	return_value = ""
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	for unit in units:
		if system.tag.read(str(unit["fullPath"]) + "/capabilities/isDefault").value:
			return_value = system.tag.read(str(unit["fullPath"]) + "/name").value
	return return_value

def get_unit_from_capability(prebatch_path, prebatch_name, capability):
	# Don't consider this function in the logger's scope; it would produce too much detail.
	# If there's no unit with this capability, return the default unit.
	return_value = ""
	units_path = prebatch_path + "Units/"
	units = system.tag.browse(path=units_path, recursive=False)
	for unit in units:
		if system.tag.read(str(unit["fullPath"]) + "/capabilities/" + capability).value:
			return_value = system.tag.read(str(unit["fullPath"]) + "/name").value
	if return_value == "":
		return_value = get_default_unit(prebatch_path, prebatch_name)
		if LOG_INFO_EVENTS:
			logger = system.util.getLogger(LOGGER_NAME)
			logger.infof("[%s] get_unit_from_capability() [do]: no unit with the capability %s found; the default unit was assigned (%s)", prebatch_name, capability, return_value)
			logger = None
	return return_value

def set_base_execution_plan(prebatch_path, prebatch_name):
	import time
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
				process_unit = get_default_unit(prebatch_path, prebatch_name)
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
					# If there's a solid in the position, force the type to solid and the unit to common.
					if component_type == 1:
						system.tag.writeBlocking(position_path + "type", 1)
						process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "common")
				# Set the new value for the component's property and the accumulated data.
				system.tag.writeBlocking(position_path + "components", components)
				system.tag.writeBlocking(position_path + "mass", mass)
				system.tag.writeBlocking(position_path + "water", water)
				# Hard dissolving solid.
				if system.tag.read(component_path + "hardDissolving").value:
					system.tag.writeBlocking(position_path + "hardDissolving", True)
					process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "hardDissolving")
				# Vacuum pump.
				if system.tag.read(component_path + "vacuumPump").value:
					system.tag.writeBlocking(position_path + "vacuumPump", True)
					process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "vacuumPump")
				# IBC.
				if system.tag.read(component_path + "IBC").value:
					system.tag.writeBlocking(position_path + "IBC", True)
					process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "IBC")
				# Liquids tank.
				if system.tag.read(component_path + "liquidsTank").value:
					system.tag.writeBlocking(position_path + "liquidsTank", True)
					process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "liquidsTank")
				# Bayonet.
				if system.tag.read(component_path + "bayonet").value:
					system.tag.writeBlocking(position_path + "bayonet", True)
					process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "bayonet")
				# Heating.
				if system.tag.read(component_path + "requiresHeating").value:
					system.tag.writeBlocking(position_path + "requiresHeating", True)
					process_unit = get_unit_from_capability(prebatch_path, prebatch_name, "requiresHeating")
				# Finally, assign the process unit to the position.
				if first_item:
					system.tag.writeBlocking(position_path + "processUnit", process_unit)
				first_item = False
	except:
		logger.errorf("[%s] set_base_execution_plan() [error]: %s", prebatch_name, str(sys.exc_info()))
	finally:
		if LOG_INFO_EVENTS:
			recipe_name = system.tag.read(prebatch_path + "Process/baseRecipe/recipeName").value
			logger.infof("[%s] set_base_execution_plan() for %s [end]", prebatch_name, recipe_name)
		logger = None

def set_unit_limit(prebatch_path, prebatch_name, tank_path):
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
					if conc_type == 1:
						# Prevent a wrong unit configuration for a solid concentrate (the minAgitationVolume tag must exist in the right unit).
						unit_min_agitation_volume = system.tag.read(pu_par_path + "minAgitationVolume").value
						if unit_min_agitation_volume is not None:
							pu_min_water_volume = unit_min_agitation_volume
					# Compare the calculated water volume with the minimum agitation volume required for the unit.
					# Liquids will always take the calculated water volume.
					if pu_min_water_volume < calculated_water:
						pu_min_water_volume = calculated_water
					calculated_water = pu_min_water_volume + system.tag.read(pu_par_path + "rinseVolume").value
				prebatch_water += calculated_water
			recipe_water = system.tag.read(recipe_path + "water").value * test_units
			required_water = tank_agitation_water + sweetener_water + prebatch_water
		min_units = 1
		if test_units < max_units:
			min_units = test_units + 1
		if min_units < 1:
			min_units = 1
		logger.infof("[%s] set_unit_limit() [do]: min_units: %d, volume: %.2f L", prebatch_name, min_units, recipe_volume * min_units)
		system.tag.write(prebatch_path + "Process/userUnits.EngLow", min_units)
		system.tag.write(prebatch_path + "Process/userUnits.EngHigh", max_units)
		system.tag.write(prebatch_path + "Process/userUnits", min_units)
		system.tag.write(prebatch_path + "Process/unitLimitSet", True)
	except:
		logger.errorf("[%s] set_unit_limit() [error]: %s", prebatch_name, str(sys.exc_info()))
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] set_unit_limit() for %s [end]", prebatch_name, recipe_name)
		logger = None

def calculate(prebatch_path, prebatch_name, tank_path, units):
	import math
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
			logger.infof("[%s] calculate() [do]: recipeId: %s, recipeName: %s, units: %d", prebatch_name, recipe_id, recipe_name, units)
		# Update the production recipe.
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
			# Initialize the number of instances for this calculated position.
			position_instances = 1
			# Load evaluation data.
			process_unit = system.tag.read(current_base_position_path + "processUnit").value
			# Empty slots will have the Process Unit tag equal to "".
			if process_unit != "":
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
				if conc_type == 1:
					# Prevent a wrong unit configuration for a solid concentrate (the minAgitationVolume tag must exist in the right unit).
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
				system.tag.writeBlocking(current_production_position_path + "water", calculated_water)
				if LOG_INFO_EVENTS:
					logger.infof("[%s] calculate() [do]: unit %s found for %s; cycles = %d", prebatch_name, process_unit, components, int(cycles))
				copy_position(current_base_position_path, current_production_position_path, cycles)
				system.tag.writeBlocking(prebatch_path + "maxPosition", i)
	except:
		logger.errorf("[%s] calculate() [error]: %s", prebatch_name, str(sys.exc_info()))
	finally:
		if LOG_INFO_EVENTS:
			logger.infof("[%s] calculate() [end]", prebatch_name)
		del logger

def save_process_data():
	logger = system.util.getLogger(LOGGER_NAME)
	logger.info("[Paragon] save_process_data() [start]")
	current_id = system.tag.read("Production/Paragon/Process/processId").value
	if (current_id == 0):
		database = "Process"
		headers_table = system.db.runQuery("SELECT process_id FROM pb_recipes_executed ORDER BY process_id DESC LIMIT 1", database)
		process_id = headers_table[0]["process_id"] + 1
		tag_path = "Production/Paragon/Process/recipe/"
		recipe_id = system.tag.read(tag_path + "id").value
		recipe_name = system.tag.read(tag_path + "name").value
		recipe_density = system.tag.read(tag_path + "density").value
		version = system.tag.read(tag_path + "version").value
		tank = system.tag.read("Production/Paragon/Process/tank").value
		units = system.tag.read("Production/Paragon/Process/units").value
		user_name = system.tag.read("Production/Paragon/Process/userName").value
		update_query = "INSERT INTO pb_recipes_executed (prebatch, tank, process_id, recipe_id, version, units, user_name"
		for i in range(POSITION_SLOTS):
			update_query += ", c" + ("%02d" % (i + 1)) + "_version" 
		update_query += ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		system.db.runPrepUpdate(update_query, [1, tank, process_id, recipe_id, version, units, user_name, system.tag.read(tag_path + "Components/c01/version").value, system.tag.read(tag_path + "Components/c02/version").value, system.tag.read(tag_path + "Components/c03/version").value, system.tag.read(tag_path + "Components/c04/version").value, system.tag.read(tag_path + "Components/c05/version").value, system.tag.read(tag_path + "Components/c06/version").value, system.tag.read(tag_path + "Components/c07/version").value, system.tag.read(tag_path + "Components/c08/version").value, system.tag.read(tag_path + "Components/c09/version").value, system.tag.read(tag_path + "Components/c10/version").value, system.tag.read(tag_path + "Components/c11/version").value, system.tag.read(tag_path + "Components/c12/version").value, system.tag.read(tag_path + "Components/c13/version").value, system.tag.read(tag_path + "Components/c14/version").value, system.tag.read(tag_path + "Components/c15/version").value, system.tag.read(tag_path + "Components/c16/version").value], database)
		# Update the tank's online contents.
		# tank_object_name = system.tag.read("Production/Paragon/Process/tankObjectName").value
		# system.tag.write("Production/SyrupRoom/Tanks/" + tank_object_name + "/recipe/recipeId", recipe_id)
		# system.tag.write("Production/SyrupRoom/Tanks/" + tank_object_name + "/density", recipe_density)
		# Indicate the process was stored.
		system.tag.write("Production/Paragon/Process/processId", process_id)
		system.tag.write("Production/Paragon/Process/processStored", True)
		logger.infof("[Paragon] save_process_data() [do]: recipeId: %s, recipeName: %s, processId: %d", recipe_id, recipe_name, process_id)
	else:
		logger.info("[Paragon] save_process_data() [do]: id already assigned")
	logger.info("[Paragon] save_process_data() [end]")
	del logger

def coordinate():
	import time
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	# General coordination.
	if (process_id > 0):
		started = system.tag.read("Production/Paragon/Process/ProgParagon/Status/Running").value
		confirmed = system.tag.read("Production/Paragon/Process/operatorConfirmation").value
		aborted = system.tag.read("Production/Paragon/Process/abort").value
		concentrate_transferred = system.tag.read("Production/Paragon/Process/concentrateTransferred").value
		if (started and confirmed and not(aborted) and not (concentrate_transferred)):		
			coordinate_t01()
			coordinate_t02()
			coordinate_b01()
			coordinate_tn01()

def module_available(position):
	logger = system.util.getLogger(LOGGER_NAME)
	logger.infof("[Paragon] module_available(position: %d) [start]", position)
	process_unit = system.tag.read("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/processUnit").value	
	result = True
	# Tank T01.
	if (process_unit == "T01"):
		logger.infof("[Paragon] module_available(position: %d) [do]: current position in T-01: %d (%s)", position, system.tag.read("Production/Paragon/Tanks/T01/executionPosition/cition").value, system.tag.read("Production/Paragon/Tanks/T01/executionPosition/components").value)
		if (system.tag.read("Production/Paragon/Tanks/T01/executionPosition/cition").value != 0):
			result = False
	# Tank T02.
	if (process_unit == "T02"):
		logger.infof("[Paragon] module_available(position: %d) [do]: current position in T-02: %d (%s)", position, system.tag.read("Production/Paragon/Tanks/T02/executionPosition/cition").value, system.tag.read("Production/Paragon/Tanks/T02/executionPosition/components").value)
		if (system.tag.read("Production/Paragon/Tanks/T02/executionPosition/cition").value != 0):
			result = False
	# Bayonet B01.
	if (process_unit == "B01"):
		logger.infof("[Paragon] module_available(position: %d) [do]: current position in B-01: %d (%s)", position, system.tag.read("Production/Paragon/Tanks/B01/executionPosition/cition").value, system.tag.read("Production/Paragon/Tanks/B01/executionPosition/components").value)
		if (system.tag.read("Production/Paragon/Tanks/B01/executionPosition/cition").value != 0):
			result = False				
	# Liquids tank TN01.
	if (process_unit == "TN01"):
		logger.infof("[Paragon] module_available(position: %d) [do]: current position in TN-01: %d (%s)", position, system.tag.read("Production/Paragon/Tanks/TN01/executionPosition/cition").value, system.tag.read("Production/Paragon/Tanks/B01/executionPosition/components").value)
		if (system.tag.read("Production/Paragon/Tanks/B01/executionPosition/cition").value != 0):
			result = False				
	logger.infof("[Paragon] module_available(position: %d) [do]: unit: %s, result: %s", position, process_unit, result)
	logger.infof("[Paragon] module_available(position: %d) [end]", position)
	return result

def coordinate_t01():
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	module_path = "Production/Paragon/Process/T01/"
	# Obtain the components" position.
	position = system.tag.read(module_path + "positionObject/cition").value
	if (position > 0):
		logger = system.util.getLogger(LOGGER_NAME)
		database = "Process"
		components = system.tag.read(module_path + "positionObject/components").value
		started = system.tag.read(module_path + "start").value
		water_added = system.tag.read(module_path + "waterComplete").value
		concentrate_added = system.tag.read(module_path + "concentrateAdded").value
		agitated = system.tag.read(module_path + "agitationDone").value
		transferred = system.tag.read(module_path + "transferred").value
		progress_table = system.db.runQuery("SELECT * FROM pb_recipes_progress_sorted WHERE process_id = " + ("%d" % process_id) + " AND position = " + ("%d" % position), database)
		# Step 1: started.
		if (started and not(step_stored(1, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 1], database)
			logger.infof("[Paragon] coordinate_t01 [do]: update STARTED status for %s", components)	
		# Step 2: water added.
		if (started and water_added and not(step_stored(2, progress_table))):
			water_accum = system.tag.read(module_path + "waterAccum").value
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, water) VALUES (?, ?, ?, ?)", [process_id, position, 2, water_accum], database)
			logger.infof("[Paragon] coordinate_t01 [do]: update WATER ADDED status for %s [%f L]", components, water_accum)	
		# Step 3: concentrate added.
		if (started and concentrate_added and not(step_stored(3, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 3], database)
			logger.infof("[Paragon] coordinate_t01 [do]: update CONCENTRATE ADDED status for %s", components)	
		# Step 4: agitation concluded.
		if (started and agitated and not(step_stored(4, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 4], database)
			logger.infof("[Paragon] coordinate_t01 [do]: update AGITATION CONCLUDED status for %s", components)	
		# Step 5: concentrate transferred.
		if (started and transferred and not(step_stored(5, progress_table))):
			total_water = system.tag.read(module_path + "waterTotal").value
			if (total_water > 0):
				system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, water) VALUES (?, ?, ?, ?)", [process_id, position, 5, total_water], database)
				# system.tag.write("Production/Paragon/Process/T01/transferredConfirmation", 1)
				logger.infof("[Paragon] coordinate_t01 [do]: update TRANSFERRED status for %s [%f L", components, total_water)	
		del logger

def coordinate_t02():
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	module_path = "Production/Paragon/Process/T02/"
	# Obtain the components" position.
	position = system.tag.read(module_path + "positionObject/cition").value
	if (position > 0):
		logger = system.util.getLogger(LOGGER_NAME)
		database = "Process"
		components = system.tag.read(module_path + "positionObject/components").value
		started = system.tag.read(module_path + "start").value
		water_added = system.tag.read(module_path + "waterComplete").value
		concentrate_added = system.tag.read(module_path + "concentrateAdded").value
		agitated = system.tag.read(module_path + "agitationDone").value
		transferred = system.tag.read(module_path + "transferred").value
		progress_table = system.db.runQuery("SELECT * FROM pb_recipes_progress_sorted WHERE process_id = " + ("%d" % process_id) + " AND position = " + ("%d" % position), database)
		# Step 1: started.
		if (started and not(step_stored(1, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 1], database)
			logger.infof("[Paragon] coordinate_t02 [do]: update STARTED status for %s", components)	
		# Step 2: water added.
		if (started and water_added and not(step_stored(2, progress_table))):
			water_accum = system.tag.read(module_path + "waterAccum").value
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, water) VALUES (?, ?, ?, ?)", [process_id, position, 2, water_accum], database)
			logger.infof("[Paragon] coordinate_t02 [do]: update WATER ADDED status for %s [%f L]", components, water_accum)	
		# Step 3: concentrate added.
		if (started and concentrate_added and not(step_stored(3, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 3], database)
			logger.infof("[Paragon] coordinate_t02 [do]: update CONCENTRATE ADDED status for %s", components)	
		# Step 4: agitation concluded.
		if (started and agitated and not(step_stored(4, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 4], database)
			logger.infof("[Paragon] coordinate_t02 [do]: update AGITATION CONCLUDED status for %s", components)	
		# Step 5: concentrate transferred.
		if (started and transferred and not(step_stored(5, progress_table))):
			total_water = system.tag.read(module_path + "waterTotal").value
			if (total_water > 0):
				system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, water) VALUES (?, ?, ?, ?)", [process_id, position, 5, total_water], database)
				# system.tag.write("Production/Paragon/Process/T02/transferredConfirmation", 1)
				logger.infof("[Paragon] coordinate_t02 [do]: update TRANSFERRED status for %s [%f L", components, total_water)	
		del logger

def coordinate_b01():
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	module_path = "Production/Paragon/Process/B01/"
	# Obtain the components" position.
	position = system.tag.read(module_path + "positionObject/cition").value
	if (position > 0):
		logger = system.util.getLogger(LOGGER_NAME)
		database = "Process"
		components = system.tag.read(module_path + "positionObject/components").value
		started = system.tag.read(module_path + "start").value
		finalize = system.tag.read(module_path + "transferred").value
		progress_table = system.db.runQuery("SELECT * FROM pb_recipes_progress_sorted WHERE process_id = " + ("%d" % process_id) + " AND position = " + ("%d" % position), database)
		# Step 1: started.
		if (started and not(step_stored(1, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 1], database)
			logger.infof("[Paragon] coordinate_b01 [do]: update STARTED status for %s", components)	
		# Step 5: concentrate transferred.
		if (finalize and not(step_stored(5, progress_table))):
			rinse_accum = system.tag.read(module_path + "waterAccum").value
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, water) VALUES (?, ?, ?, ?)", [process_id, position, 5, rinse_accum], database)
			# system.tag.write("Production/Paragon/Process/B01/transferredConfirmation", 1)
			logger.infof("[Paragon] coordinate_b01 [do]: update TRANSFERRED status for %s", components)	
		del logger

def coordinate_tn01():
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	module_path = "Production/Paragon/Process/TN01/"
	# Obtain the components" position.
	position = system.tag.read(module_path + "executionPosition/cition").value
	if (position > 0):
		logger = system.util.getLogger(LOGGER_NAME)
		database = "Process"
		components = system.tag.read(module_path + "executionPosition/components").value
		started = system.tag.read(module_path + "start").value
		finalize = system.tag.read(module_path + "transferred").value
		progress_table = system.db.runQuery("SELECT * FROM pb_recipes_progress_sorted WHERE process_id = " + ("%d" % process_id) + " AND position = " + ("%d" % position), database)
		# Step 1: started.
		if (started and not(step_stored(1, progress_table))):
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step) VALUES (?, ?, ?)", [process_id, position, 1], database)
			logger.infof("[Paragon] coordinate_tn01 [do]: update STARTED status for %s", components)	
		# Step 5: concentrate transferred.
		if (finalize and not(step_stored(5, progress_table))):
			water_accum = system.tag.read(module_path + "waterAccum").value
			rinse_accum = system.tag.read(module_path + "Par/rinseAccum").value
			total_water = water_accum + rinse_accum
			system.db.runPrepUpdate("INSERT INTO pb_recipes_progress (process_id, position, step, water) VALUES (?, ?, ?, ?)", [process_id, position, 5, total_water], database)
			# system.tag.write("Production/Paragon/Process/TN01/transferredConfirmation", 1)
			logger.infof("[Paragon] coordinate_tn01 [do]: update TRANSFERRED status for %s", components)	
		del logger

def step_stored(step, progress_table):
	result = False
	for row_index in range(len(progress_table)):
		if (step == progress_table[row_index]["step"]):
			result = True
	return result 

def initialize_module(position):
	logger = system.util.getLogger(LOGGER_NAME)
	logger.infof("[Paragon] initialize_module(position: %d) [start]", position)
	initialization_path = ""
	unit_to_initialize = ""
	# Tank T-01.
	if (system.tag.read("Production/Paragon/Tanks/T01/executionPosition/cition").value == position):
		initialization_path = "Production/Paragon/Tanks/T01/"
		unit_to_initialize = "T-01"
	# Tank T-02.
	if (system.tag.read("Production/Paragon/Tanks/T02/executionPosition/cition").value == position):
		initialization_path = "Production/Paragon/Tanks/T02/"
		unit_to_initialize = "T-02"
	# Bayonet 1.
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
	# Initialize the processor"s flags.
	system.tag.writeSynchronous(initialization_path + "initializeProcessor", False)
	logger.infof("[Paragon] initialize_module(position: %d, unit %s) [end]", position, unit_to_initialize)
	del logger

def process_component(position, in_transfer_position):
	logger = system.util.getLogger(LOGGER_NAME)
	logger.infof("[Paragon] process_component(position: %d, in_transfer_position: %s) [start]", position, in_transfer_position)
	process_unit = system.tag.read("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/processUnit").value
	# Tank T-01.
	if (process_unit == "T-01"):
		# Copy the position if required.
		if (system.tag.read("Production/Paragon/Tanks/T01/executionPosition/cition").value != position):
			copy_position("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/", "Production/Paragon/Tanks/T01/executionPosition/", 1)
		system.tag.writeSynchronous("Production/Paragon/Tanks/T01/inTransferPosition", in_transfer_position, 5000)
	# Tank T-02.
	if (process_unit == "T-02"):
		# Copy the position if required.
		if (system.tag.read("Production/Paragon/Tanks/T02/executionPosition/cition").value != position):
			copy_position("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/", "Production/Paragon/Tanks/T02/executionPosition/", 1)
		system.tag.writeSynchronous("Production/Paragon/Tanks/T02/inTransferPosition", in_transfer_position, 5000)
	# Bayonet.
	if (process_unit == "B-01"):
		# Copy the position if required.
		if (system.tag.read("Production/Paragon/Tanks/B01/executionPosition/cition").value != position):
			copy_position("Production/Paragon/Process/executionPlan/cition" + ("%02d" % position) + "/", "Production/Paragon/Tanks/B01/executionPosition/", 1)
		system.tag.writeSynchronous("Production/Paragon/Tanks/B01/inTransferPosition", in_transfer_position, 5000)
	logger.infof("[Paragon] process_component(position: %d, in_transfer_position: %s) [end]", position, in_transfer_position)
	del logger

def copy_position(origin, destination, partitions):
	logger = system.util.getLogger(LOGGER_NAME)
	logger.infof("[Paragon] copy_position(origin: %s, destination: %s) [start]", origin, destination)
	# Verify that all properties from the object are in this function.
	# Certain tags have to be written synchronously to avoid write speed problems.
	system.tag.writeSynchronous(destination + "position", system.tag.read(origin + "position").value, 5000)
	system.tag.writeSynchronous(destination + "processUnit", system.tag.read(origin + "processUnit").value, 5000)
	system.tag.write(destination + "agitationAutomatic", system.tag.read(origin + "agitationAutomatic").value)
	system.tag.write(destination + "agitationDuration", system.tag.read(origin + "agitationDuration").value)
	system.tag.write(destination + "baseMass", system.tag.read(origin + "baseMass").value)
	system.tag.write(destination + "baseWater", system.tag.read(origin + "baseWater").value)
	system.tag.write(destination + "calculatedMass", system.tag.read(origin + "calculatedMass").value / partitions)
	system.tag.write(destination + "calculatedWater", system.tag.read(origin + "calculatedWater").value / partitions)
	system.tag.write(destination + "cycles", partitions)
	system.tag.write(destination + "changeAllowed", system.tag.read(origin + "changeAllowed").value)
	system.tag.writeSynchronous(destination + "components", system.tag.read(origin + "components").value, 5000)
	system.tag.write(destination + "type", system.tag.read(origin + "type").value)
	logger.infof("[Paragon] copy_position(origin: %s, destination: %s) [do (%s)]: unit: %s", origin, destination, system.tag.read(destination + "components").value, system.tag.read(origin + "processUnit").value)	
	logger.infof("[Paragon] copy_position(origin: %s, destination: %s) [end]", origin, destination)
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

def cancel_running_recipe():
	logger = system.util.getLogger(LOGGER_NAME)
	logger.info("[Paragon] cancel_running_recipe() [start]")	
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	if (process_id > 0):
		database = "Process"
		system.db.runPrepUpdate("INSERT INTO pb_recipes_canceled (process_id) VALUES (?)", [process_id], database)
	save_final_data_running_recipe()
	logger.info("[Paragon] cancel_running_recipe() [end]")
	del logger

def save_final_data_running_recipe():
	import time
	logger = system.util.getLogger(LOGGER_NAME)
	logger.info("[Paragon] save_final_data_running_recipe() [start]")
	store_inventory()
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	if (process_id > 0):
		tank = system.tag.read("Production/Paragon/Process/tank").value
		recipe_id = system.tag.read("Production/Paragon/Process/recipe/id").value
		recipe_name = system.tag.read("Production/Paragon/Process/recipe/name").value
		water = system.tag.read("Production/Paragon/Process/waterAccum").value
		sucrose = system.tag.read("Production/Paragon/Process/sucroseAccum").value
		fructose = system.tag.read("Production/Paragon/Process/fructoseAccum").value
		database = "Process"
		system.db.runPrepUpdate("INSERT INTO tanks_data (process_id, tank_id, recipe_id, sucrose, fructose, water) VALUES (?, ?, ?, ?, ?, ?)", [process_id, tank, recipe_id, sucrose, fructose, water], database)
		logger.infof("[Paragon] save_final_data_running_recipe() [do]: recipeId: %s, recipeName: %s, processId: %d", recipe_id, recipe_name, process_id)
	else:
		logger.info("[Paragon] save_final_data_running_recipe() [do]: no running process found")
	time.sleep(3)
	system.tag.write("Production/Paragon/Process/clear", True)
	logger.info("[Paragon] save_final_data_running_recipe() [end]")
	del logger

def check_inventory_completion():
	# Check if barcode validation is active.
	if (system.tag.read("Production/Paragon/Process/Inventory/skip").value):
		system.tag.write("Production/Paragon/Process/Inventory/correct", False)
	else:
		current_correct_flag = system.tag.read("Production/Paragon/Process/Inventory/correct").value
		result = False
		if not(system.tag.read("Production/Paragon/Process/Inventory/wrongCodesExist").value):
			result = True
			required_units = system.tag.read("Production/Paragon/Process/units").value
			database = "Process"
			table = system.db.runPrepQuery("SELECT * FROM pb_inventory_capture_detailed WHERE prebatch = 1", [], database)
			if len(table) > 0:
				tag_path = "Production/Paragon/Process/recipe/Components/"
				# Component slot loop.
				for i in range(16):
					# Each required concentrate has to be checked in the capture table.
					# The loop has to compare its existence and the unit amount.
					# Since there can be different component presentations in the same production recipe, accumulation has to be performed.
					concentrate_found = False
					current_recipe_component = system.tag.read(tag_path + "c" + ("%02d" % (i + 1)) + "/id").value
					requires_inventory_validation = not(system.tag.read(tag_path + "c" + ("%02d" % (i + 1)) + "/noInventoryValidation").value)
					if ((current_recipe_component != "-") and requires_inventory_validation):
						component_units = 0
						for row_index in range(len(table)):
							# Field loop.
							for j in range(5):
								current_package_component_id = table[row_index]["c" + ("%02d" % (j + 1)) + "_id"]
								if (current_package_component_id == current_recipe_component):
									component_units += table[row_index]["units_total"]
						if (required_units == component_units):
							concentrate_found = True
					else:
						concentrate_found = True
					if not(concentrate_found):
						result = False
			else:
				result = False
			# Don"t wait for the garbage collector to release the table"s used memory.
			del table	
		system.tag.write("Production/Paragon/Process/Inventory/correct", result)
		# Send to the logger only if there"s a change in the correct flag.
		if (current_correct_flag != result):
			logger = system.util.getLogger(LOGGER_NAME)
			logger.infof("[Paragon] check_inventory_completion() [do]: correct: %s", result)	
			del logger

def store_inventory():
	logger = system.util.getLogger(LOGGER_NAME)
	logger.info("[Paragon] store_inventory() [start]")	
	# Transfers the records from the capture table to the history one.
	process_id = system.tag.read("Production/Paragon/Process/processId").value
	database = "Process"
	capture_table = system.db.runPrepQuery("SELECT * FROM pb_inventory_capture WHERE prebatch = 1", [], database)
	tx_id = system.db.beginTransaction(database, timeout = 5000)
	for row_index in range(len(capture_table)):
		local_row = capture_table[row_index]
		# Update history.
		update_query = "INSERT INTO pb_inventory_history (process_id, capture_host, capture_user, presentation_id, presentation_batch, presentation_expiration, presentation_serial, update_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
		system.db.runPrepUpdate(update_query, [process_id, local_row["capture_host"], local_row["capture_user"], local_row["presentation_id"], local_row["presentation_batch"], local_row["presentation_expiration"], local_row["presentation_serial"], local_row["update_time"]], database, tx_id)
		# Update warehouse data.
		# update_query = "UPDATE pb_inventory_warehouse SET obsolete = TRUE WHERE presentation_id = ? AND presentation_batch = ? AND presentation_serial = ?"
		# system.db.runPrepUpdate(update_query, [local_row["presentation_id"], local_row["presentation_batch"], local_row["presentation_serial"]], database, tx_id)
		# update_query = "INSERT INTO pb_inventory_warehouse (presentation_id, presentation_batch, presentation_serial, presentation_expiration, comments) VALUES (?, ?, ?, ?, ?)"
		# system.db.runPrepUpdate(update_query, [local_row["presentation_id"], local_row["presentation_batch"], local_row["presentation_serial"], local_row["presentation_expiration"], "Salida por consumo"], database, tx_id)
	system.db.commitTransaction(tx_id)
	system.db.closeTransaction(tx_id)
	# Don"t wait for the garbage collector to release the table"s used memory.
	del capture_table
	system.db.runPrepUpdate("DELETE FROM pb_inventory_capture WHERE prebatch = 1", [], database)
	logger.info("[Paragon] store_inventory() [end]")	
	del logger

if __name__ == '__main__':
	mark_process_start("Prebatch 1", "Tanque 4")