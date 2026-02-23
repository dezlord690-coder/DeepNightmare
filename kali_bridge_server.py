import asyncio
import json
import subprocess
from aiohttp import web

# This server listens for instructions from the Windows Brain
HOST = '127.0.0.1'
PORT = 9001

async def execute_tool(request):
    """
    Receives a command, executes it in Kali, and returns the output.
    Supports asynchronous execution so multiple tools can run at once.
    """
    data = await request.json()
    command = data.get("command")
    mission_id = data.get("mission_id")

    print(f"[*] Brain signaling: {command}")

    # Process start - Using Async Subprocess to prevent blocking
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Wait for completion (or you can modify this to stream live logs)
    stdout, stderr = await process.communicate()
    
    result = {
        "mission_id": mission_id,
        "stdout": stdout.decode().strip(),
        "stderr": stderr.decode().strip(),
        "exit_code": process.returncode
    }

    return web.json_response(result)

async def health_check(request):
    return web.Response(text="DeepNightmare Bridge: ONLINE")

app = web.Application()
app.add_routes([
    web.post('/exec', execute_tool),
    web.get('/status', health_check)
])

if __name__ == '__main__':
    print(f"🚀 DeepNightmare Kali Bridge starting on {HOST}:{PORT}...")
    web.run_app(app, host=HOST, port=PORT)
