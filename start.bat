@echo off
echo Starting TiO Platform...

:: Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: Ensure spacy model
python -m spacy download en_core_web_sm

:: Start backend in new window
start "TiO Backend" cmd /k "python main.py"

:: Start frontend
cd frontend
if not exist node_modules (
    npm install
)
npm run dev
