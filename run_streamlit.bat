@echo off
CHCP 65001 > NUL

REM Navegar al directorio del script
pushd "%~dp0"

echo Iniciando la aplicación Streamlit...
streamlit run streamlit_app.py

REM Volver al directorio original
popd

pause