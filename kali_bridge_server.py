import asyncio
import json
import subprocess
import datetime
from aiohttp import web

HOST = '127.0.0.1'
PORT = 9001

async def execute_tool(request):
    """
    Executes commands in Kali. 
    Supports 'Fire-and-Forget' for multi-terminal workflows.
    """
    data = await request.json()
    command = data.get("command")
    mission_id = data.get("mission_id")
    is_async = data.get("async_mode", False)

    print(f"[*] [{datetime.datetime.now().strftime('%H:%M:%S')}] Mission {mission_id} -> {command}")

    if is_async:
        # FIRE-AND-FORGET: Start the process and return immediately
        asyncio.create_task(run_background_process(command, mission_id))
        return web.json_response({
            "status": "Task Started",
            "command": command,
            "info": "Execution running in background terminal."
        })
    
    # SYNC MODE: Wait and return result (Standard for quick recon)
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    return web.json_response({
        "mission_id": mission_id,
        "stdout": stdout.decode(errors='ignore').strip(),
        "stderr": stderr.decode(errors='ignore').strip(),
        "exit_code": process.returncode
    })

async def run_background_process(command, mission_id):
    """Handles long-running tools without blocking the Bridge."""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    # In a full setup, you could trigger a webhook here or update a shared log file
    print(f"[✔] Background Task Finished: {command[:30]}... (Mission: {mission_id})")

async def health_check(request):
    return web.Response(text="DeepNightmare Bridge: ONLINE")

app = web.Application()
app.add_routes([
    web.post('/exec', execute_tool),
    web.get('/status', health_check)
])

if __name__ == '__main__':
    print(f"🚀 DeepNightmare Kali Bridge starting on {HOST}:{PORT}...")
    print(f"[*] Multi-Terminal Support: ENABLED")
    web.run_app(app, host=HOST, port=PORT)
