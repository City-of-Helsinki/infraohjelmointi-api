-- Round costForecast to whole numbers, in order to then run 0056_alter_project_costforecast.py migration to PositiveIntegerField
-- This needs to be done prior to migrating, otherwise costForecast already in DB will be deleted
UPDATE infraohjelmointi_api_project
SET "costForecast" = ROUND("costForecast");