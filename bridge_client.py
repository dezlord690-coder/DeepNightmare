import requests
import json
import logging
import asyncio
import aiohttp

class KaliBridgeClient:
    def __init__(self, host="127.0.0.1", port=9001):
        self.base_url = f"http://{host}:{port}"
        self.timeout = 600  # 10 minutes for deep scans
        
    async def check_connection(self):
        """Verifies the Kali Bridge is active before starting mission."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/status", timeout=5) as resp:
                    return resp.status_code == 200
            except:
                return False

    async def send_command_async(self, mission_id, command):
        """
        Non-blocking command dispatch. 
        Allows the Brain to keep working while Kali runs the tool.
        """
        payload = {
            "mission_id": mission_id,
            "command": command,
            "async_mode": True  # Tells the server to spawn a new terminal window
        }
        
        print(f"[BRIDGE] 🚀 Spawning Terminal in Kali: {command}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/exec", 
                    json=payload, 
                    timeout=self.timeout
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data
                    else:
                        return {"stdout": "", "stderr": f"Bridge Error: {resp.status}"}
            except asyncio.TimeoutError:
                return {"stdout": "", "stderr": "Error: Command timed out on Kali side."}
            except Exception as e:
                return {"stdout": "", "stderr": f"Bridge Connection Failed: {str(e)}"}

    def send_command_sync(self, mission_id, command):
        """Standard blocking call for quick verification commands."""
        payload = {"mission_id": mission_id, "command": command}
        try:
            response = requests.post(f"{self.base_url}/exec", json=payload, timeout=30)
            return response.json()
        except Exception as e:
            return {"stdout": "", "stderr": str(e)}

# Professional Implementation Note:
# Use 'send_command_async' for Phase 1 & 2 tools (nmap, ffuf, subfinder).
# Use 'send_command_sync' for Phase 3 exploitation steps that need immediate feedback.
