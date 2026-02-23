import asyncio
import json
import time
import aiohttp
from database_manager import MissionVault
from neural_shield import NeuralShield
from motivation_engine import MotivationEngine

# --- CONFIGURATION ---
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
# Switching to 0.5B model to save your CPU and stop the lag
MODEL_NAME = "qwen2.5-coder:0.5b" 
KALI_BRIDGE_URL = "http://127.0.0.1:9001/exec"

class DeepNightmareApex:
    def __init__(self, target_url):
        self.target = target_url
        self.vault = MissionVault()
        self.shield = NeuralShield()
        self.motivator = MotivationEngine()
        self.is_running = True
        
        print(f"[*] Connection established to Light-Brain Engine ({MODEL_NAME})")

    async def get_ollama_response(self, prompt, system_context=""):
        """Talks to the Ollama API with high-speed local settings"""
        payload = {
            "model": MODEL_NAME,
            "prompt": f"{system_context}\n\n{prompt}",
            "stream": False,
            "options": {
                "num_thread": 4, # Limits CPU cores to prevent 100% usage lockup
                "temperature": 0.3
            }
        }
        
        print(f"    ... AI is generating (Light-Mode Active) ...", end="\r")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Shorter timeout because 0.5B should be fast
                async with session.post(OLLAMA_API_URL, json=payload, timeout=60) as resp:
                    data = await resp.json()
                    response_text = data.get('response', "").strip()
                    
                    # Clear the thinking line
                    print(" " * 60, end="\r") 
                    return response_text
            except Exception as e:
                return f"Error connecting to Ollama: {str(e)}"

    async def run_mission(self):
        print(f"\n[!] DEEPNIGHTMARE APEX ONLINE | TARGET: {self.target}")
        last_success_time = time.time()

        while self.is_running:
            # 1. PULL SHARED CONTEXT
            history_rows = self.vault.get_brain_context(mission_id=1)
            history_text = "\n".join([f"{h['brain_source']}: {h['command_executed']} -> {h['status']}" for h in history_rows[-5:]])

            # 2. STRATEGIC REASONING
            print(f"[*] Analyzing target: {self.target}")
            strategy_prompt = f"Target: {self.target}\nPast Actions:\n{history_text}\nTask: Suggest a quick recon command."
            strategy = await self.get_ollama_response(strategy_prompt, "Act as a cyber-security expert. Be brief.")

            # 3. TACTICAL EXECUTION
            tactical_prompt = f"Strategy: {strategy}\nProvide the exact Linux command for Kali."
            generated_cmd = await self.get_ollama_response(tactical_prompt, "Provide ONLY the command string. No explanation.")

            # 4. NEURAL SHIELD VALIDATION
            is_safe, final_cmd = self.shield.validate_command(generated_cmd, self.load_manifest())
            
            if is_safe:
                # 5. EXECUTION VIA KALI BRIDGE
                print(f"\n[>] Strategy: {strategy[:100]}...") 
                print(f"[>] EXECUTING: {final_cmd}")
                
                result = await self.execute_on_kali(final_cmd)
                
                # 6. SANITIZATION & LOGGING
                stdout_data = result.get('stdout', '') if result else 'No response from bridge'
                safe_output = self.shield.sanitize_output(stdout_data)
                self.vault.log_terminal_action(1, "DeepNightmare", final_cmd, safe_output, "Success")
                
                # 7. MOTIVATION CHECK
                if "success" in safe_output.lower() or "open" in safe_output.lower():
                    last_success_time = time.time()
                    print(self.motivator.get_status_message(last_success_time, success_found=True))
                else:
                    print(self.motivator.get_status_message(last_success_time))

            # Increased wait time to 15 seconds to let your CPU cool down
            print("\n[*] Waiting 15s for CPU cooldown...")
            await asyncio.sleep(15) 

    async def execute_on_kali(self, command):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(KALI_BRIDGE_URL, json={"command": command, "mission_id": 1}, timeout=300) as resp:
                    return await resp.json()
            except Exception as e:
                print(f"[!] Bridge Error: {str(e)}")
                return {"stdout": f"Error connecting to Kali Bridge: {str(e)}", "stderr": ""}

    def load_manifest(self):
        try:
            with open('tool_manifest.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

if __name__ == "__main__":
    # Dynamic target input
    target = input("Enter target URL/Domain: ")
    if not target:
        print("[!] No target entered. Exiting.")
    else:
        apex = DeepNightmareApex(target)
        try:
            asyncio.run(apex.run_mission())
        except KeyboardInterrupt:
            print("\n[!] Shutting down Apex Orchestrator...")
