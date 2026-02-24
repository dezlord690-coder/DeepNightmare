@echo off
SETLOCAL
TITLE DEEPNIGHTMARE - MISSION CONTROL
COLOR 0B

echo ======================================================
echo          DEEPNIGHTMARE SOVEREIGN APEX v5.0
echo ======================================================

echo [!] STAGE 1: Starting Kali Bridge in WSL...
:: Ensure the path matches your WSL home directory structure
start "DEEPNIGHTMARE_BRIDGE" wsl python3 /home/user/deepnightmare/kali_bridge_server.py

echo [!] STAGE 2: Waiting for Bridge to stabilize (5s)...
timeout /t 5 /nobreak > nul

echo [!] STAGE 3: Verifying Vault Database...
if not exist "deepnightmare_vault.db" (
    echo [?] No Vault detected. Apex will initialize deepnightmare_vault.db...
) else (
    echo [✔] Vault Integrity Verified.
)

echo [!] STAGE 4: Verifying Ollama Brain (Qwen2.5-Coder)...
ollama list | findstr "qwen2.5-coder:0.5b" > nul
if %errorlevel% neq 0 (
    echo [!] Brain Missing! Downloading Qwen2.5-Coder-0.5B...
    ollama pull qwen2.5-coder:0.5b
)

echo [!] STAGE 5: Launching Apex Orchestrator...
:: Using 'python' for Windows-side execution
python ares_apex.py

echo.
echo [!] Mission Terminated or Manually Interrupted.
echo [!] Check terminal_logs in Vault for forensic data.
pause
