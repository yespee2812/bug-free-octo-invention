@echo off
setlocal

python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
if errorlevel 1 (
    pip install "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"
)

echo Setup complete. Activate the virtual environment with: venv\Scripts\activate.bat
