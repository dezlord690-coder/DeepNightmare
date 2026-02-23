import requests
import json
import logging

class KaliBridgeClient:
    def __init__(self, host="127.0.0.1", port=9001):
        self.base_url = f"http://{host}:{port}"
        self.timeout = 600  # 10 minutes for long scans like Nmap
        
    def check_connection(self):
        """Verifies the Kali Bridge is active before starting mission."""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def send_command(self, mission_id, command):
        """Sends a command to Kali and returns the raw response."""
        payload = {
            "mission_id": mission_id,
            "command": command
        }
        
        try:
            print(f"[BRIDGE] Dispatching to Kali: {command}")
            response = requests.post(
                f"{self.base_url}/exec", 
                json=payload, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"stdout": "", "stderr": f"Bridge Error: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"stdout": "", "stderr": "Error: Command timed out on Kali side."}
        except Exception as e:
            return {"stdout": "", "stderr": f"Bridge Connection Failed: {str(e)}"}

# Example Integration:
# bridge = KaliBridgeClient()
# if bridge.check_connection():
#     result = bridge.send_command(1, "whoami")
#     print(result['stdout'])
