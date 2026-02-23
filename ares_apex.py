import asyncio
import json
import time
import aiohttp
from database_manager import MissionVault
from neural_shield import NeuralShield
from motivation_engine import MotivationEngine

# --- CONFIGURATION ---
# We now point to the Ollama API instead of local file paths
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b" 
KALI_BRIDGE_URL = "http://127.0.0.1:9001/exec"

class DeepNightmareApex:
    def __init__(self, target_url):
        self.target = target_url
        self.vault = MissionVault()
        self.shield = NeuralShield()
        self.motivator = MotivationEngine()
        self.is_running = True
        
        print(f"[*] Connection established to Ollama Engine ({MODEL_NAME})")

    async def get_ollama_response(self, prompt, system_context=""):
        """Talks to the Ollama API instead of using llama-cpp-python"""
        payload = {
            "model": MODEL_NAME,
            "prompt": f"{system_context}\n\n{prompt}",
            "stream": False
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OLLAMA_API_URL, json=payload) as resp:
                    data = await resp.json()
                    # DeepSeek-R1 often includes <think> tags; we return the final answer
                    return data.get('response', "").split("</think>")[-1].strip()
            except Exception as e:
                return f"Error connecting to Ollama: {str(e)}"

    async def run_mission(self):
        print(f"\n[!] DEEPNIGHTMARE APEX ONLINE | TARGET: {self.target}")
        last_success_time = time.time()

        while self.is_running:
            # 1. PULL SHARED CONTEXT
            history_rows = self.vault.get_brain_context(mission_id=1)
            history_text = "\n".join([f"{h['brain_source']}: {h['command_executed']} -> {h['status']}" for h in history_rows[-5:]])

            # 2. STRATEGIC REASONING (Ollama/DeepSeek)
            strategy_prompt = f"Target: {self.target}\nPast Actions:\n{history_text}\nTask: Plan the next move to achieve 90% recon."
            strategy = await self.get_ollama_response(strategy_prompt, "### Instruction: Act as a Strategic Reasoner.")

            # 3. TACTICAL EXECUTION (Ollama/DeepSeek)
            tactical_prompt = f"Strategy: {strategy}\nProvide the exact Kali command to execute."
            generated_cmd = await self.get_ollama_response(tactical_prompt, "### Instruction: Provide ONLY the Linux command string.")

            # 4. NEURAL SHIELD VALIDATION
            is_safe, final_cmd = self.shield.validate_command(generated_cmd, self.load_manifest())
            
            if is_safe:
                # 5. EXECUTION VIA KALI BRIDGE
                print(f"\n[>] {strategy[:100]}...") # Print shortened strategy
                print(f"[>] EXECUTING: {final_cmd}")
                
                result = await self.execute_on_kali(final_cmd)
                
                # 6. SANITIZATION & LOGGING
                safe_output = self.shield.sanitize_output(result.get('stdout', ''))
                self.vault.log_terminal_action(1, "DeepNightmare", final_cmd, safe_output, "Success")
                
                # 7. MOTIVATION CHECK
                if "success" in safe_output.lower() or "open" in safe_output.lower():
                    last_success_time = time.time()
                    print(self.motivator.get_status_message(last_success_time, success_found=True))
                else:
                    print(self.motivator.get_status_message(last_success_time))

            await asyncio.sleep(2) # Prevent CPU throttling

    async def execute_on_kali(self, command):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(KALI_BRIDGE_URL, json={"command": command, "mission_id": 1}, timeout=300) as resp:
                    return await resp.json()
            except Exception as e:
                return {"stdout": f"Error connecting to Kali Bridge: {str(e)}", "stderr": ""}

    def load_manifest(self):
        try:
            with open('tool_manifest.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

if __name__ == "__main__":
    target = input("Enter target URL/Domain: ")
    apex = DeepNightmareApex(target)
    try:
        asyncio.run(apex.run_mission())
    except KeyboardInterrupt:
        print("\n[!] Shutting down Apex Orchestrator...")
