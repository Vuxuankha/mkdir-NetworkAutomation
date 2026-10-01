@echo off
setlocal
cd /d "%~dp0"
rem Remove only obsolete AI source modules after updating an existing installation.
for %%F in (modules\global_assistant.py modules\assistant_ui.py modules\assistant_agent.py modules\assistant_tools.py modules\ai_tasks.py modules\ai_preferences.py tests\test_assistant_agent.py tests\test_ai_tasks.py tests\test_ai_preferences.py tests\test_gemini.py tests\ui_assistant_smoke.py) do (
  if exist "%%F" del /q "%%F"
)
for %%F in (modules\__pycache__\global_assistant.*.pyc modules\__pycache__\assistant_ui.*.pyc modules\__pycache__\assistant_agent.*.pyc modules\__pycache__\assistant_tools.*.pyc modules\__pycache__\ai_tasks.*.pyc modules\__pycache__\ai_preferences.*.pyc) do (
  if exist "%%F" del /q "%%F"
)
echo Obsolete AI source modules removed. Application data is preserved.
endlocal
