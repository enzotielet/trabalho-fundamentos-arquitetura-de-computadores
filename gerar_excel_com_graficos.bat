@echo off
setlocal
cd /d "%~dp0"

REM Gera resultados_cache.csv e resultados_cache_com_graficos.xlsx
REM A pasta "resultados" deve estar ao lado deste arquivo.

python "%~dp0gerar_excel_cache_com_graficos.py" "%~dp0resultados"

pause
