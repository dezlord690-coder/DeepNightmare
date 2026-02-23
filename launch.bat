@echo off
SETLOCAL
TITLE DEEPNIGHTMARE - MISSION CONTROL

echo [!] STAGE 1: Starting Kali Bridge in WSL...
start "KALI_BRIDGE" wsl python3 /home/user/deepnightmare/kali_bridge.py

echo [!] STAGE 2: Waiting for Bridge to stabilize (5s)...
timeout /t 5 /nobreak > nul

echo [!] STAGE 3: Verifying Vault Database...
if not exist "deepnightmare_vault.db" (
    echo [?] First run detected. Initializing new Vault...
)

echo [!] STAGE 4: Launching Apex Orchestrator...
:: This starts the main loop and the Omni-Dashboard
python ares_apex.py

echo [!] Mission Terminated.
pause
