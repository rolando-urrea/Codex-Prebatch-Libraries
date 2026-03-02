# Prebatch Backend Batch Management Link function library v2.0.0 BETA.
# This set of functions allows the interaction between the Ignition Backend and Batch Management.
# To be used on Inductive Automation's Ignition platform.
#
# Rolando Urrea.
# Cobalt Processworks.
# 2026-02-28: initial release.

# CONSTANTS.
# Python 2.7 (Ignition's internal Python version, which does not support variable type forcing (VAR:type = value)).
# General.
LOG_INFO_EVENTS = True
LOGGER_NAME = "CodexPrebatchBatchLinkBackend"
# Software database specifications.
DATABASE = "Process"

def main(prebatch_path):
	prebatch_name = system.tag.read(prebatch_path + "Process/prebatchName").value
	logger = system.util.getLogger(LOGGER_NAME)
	# The Reset Alarms button in the HMI should reset the Alarmed flag.
	system_alarmed = system.tag.read(prebatch_path + "Process/backendAlarmed").value
	# Verify there's a correct configuration in the system.
	if not system_alarmed:
		# The recipe is the first variable received from the Batch Management System.
		# In case it doesn't exist, inform the user and activate the Alarmed flag.
		batch_recipe_id = system.tag.read(prebatch_path + "Process/Batch/recipeId").value
		if len(batch_recipe_id) > 2:
			recipe_name = system.db.runScalarPrepQuery("SELECT recipe_name FROM pb_recipes_current_basic WHERE recipe_id = ?", [batch_recipe_id], DATABASE)
			if recipe_name is None:
				logger.errorf("[%s] main() [error]: Batch Management Link: recipe not found: %s", prebatch_name, batch_recipe_id)
				system.tag.writeBlocking(prebatch_path + "Process/backendAlarmed", True)
			else:
				# Keep evaluating.
				backend_tank_tag = system.tag.read(prebatch_path + "Process/tank")
				if backend_tank_tag.quality.isGood:
					backend_tank = backend_tank_tag.value
					batch_tank = system.tag.read(prebatch_path + "Process/Batch/tank").value
					if batch_tank > 0:
						# Compare the Batch tank selection against the Backend.
						if batch_tank != backend_tank:
							# A tank has been selected in the Batch Management System.
							# Check if the tank is valid.
							tank_name = system.db.runScalarPrepQuery("SELECT tank_name FROM finished_syrup_tanks WHERE tank_id = ?", [batch_tank], DATABASE)
							if tank_name is not None:
								system.tag.writeBlocking(prebatch_path + "Process/tank", batch_tank)
								if LOG_INFO_EVENTS:
									logger.infof("[%s] main() [do]: Batch Management Link: tank selected: %s", prebatch_name, tank_name)
							else:
								logger.errorf("[%s] main() [error]: Batch Management Link: tank not found: %d", prebatch_name, batch_tank)
								system.tag.writeBlocking(prebatch_path + "Process/backendAlarmed", True)
						else:
							# Wait for the recipe selection.
							batch_recipe_id = system.tag.read(prebatch_path + "Process/Batch/recipeId").value
							if len(batch_recipe_id) > 2:
								backend_recipe_id = system.tag.read(prebatch_path + "Process/baseRecipe/recipeId").value
								if backend_recipe_id != batch_recipe_id:
									# A recipe was selected in the Batch Management System.
									system.tag.writeBlocking(prebatch_path + "Process/baseRecipe/recipeId", batch_recipe_id)
									if LOG_INFO_EVENTS:
										logger.infof("[%s] main() [do]: Batch Management Link: recipe selected: %s", prebatch_name, recipe_name)
								else:
									# Evaluate the unit selection.
									batch_units = system.tag.read(prebatch_path + "Process/Batch/numericUnits").value
									backend_units = system.tag.read(prebatch_path + "Process/userUnits").value
									if batch_units != backend_units:
										system.tag.writeBlocking(prebatch_path + "Process/userUnits", batch_units)
										if LOG_INFO_EVENTS:
											logger.infof("[%s] main() [do]: Batch Management Link: units set: %d", prebatch_name, batch_units)
					else:
						# Check if the tank was already initialized; otherwise, clear the Batch folder variables and initialize the local tank.
						if backend_tank != 0:
							system.tag.writeBlocking(prebatch_path + "Process/tank", 0)
							system.tag.writeBlocking(prebatch_path + "Process/Batch/recipeId", "")
							system.tag.writeBlocking(prebatch_path + "Process/Batch/stringUnits", "")
	logger = None