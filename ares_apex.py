import asyncio
import json
import time
from llama_cpp import Llama  # Requires: pip install llama-cpp-python
from database_manager import MissionVault
from neural_shield import NeuralShield
from motivation_engine import MotivationEngine

# --- CONFIGURATION ---
MODEL_PATH_DEEPSEEK = "models/deepseek-r1-1.5b-q4.gguf"
MODEL_PATH_DEEPHAT = "models/deephat-v1-q4.gguf"
KALI_BRIDGE_URL = "http://127.0.0.1:9001/exec"

class DeepNightmareApex:
    def __init__(self, target_url):
        self.target = target_url
        self.vault = MissionVault()
        self.shield = NeuralShield()
        self.motivator = MotivationEngine()
        self.is_running = True
        
        # 🧠 LOAD DUAL BRAINS (Optimized for 16GB RAM)
        # n_gpu_layers=0 for CPU-only; change to 20+ if you have an NVIDIA GPU
        print("[*] Initializing Strategic Reasoner (DeepSeek)...")
        self.reasoner = Llama(model_path=MODEL_PATH_DEEPSEEK, n_ctx=2048, n_threads=4, n_gpu_layers=0)
        
        print("[*] Initializing Tactical Executor (DeepHat)...")
        self.executor = Llama(model_path=MODEL_PATH_DEEPHAT, n_ctx=2048, n_threads=4, n_gpu_layers=0)

    async def run_mission(self):
        print(f"\n[!] DEEPNIGHTMARE APEX ONLINE | TARGET: {self.target}")
        last_success_time = time.time()

        while self.is_running:
            # 1. PULL SHARED CONTEXT (What happened in the last 5 minutes?)
            history_rows = self.vault.get_brain_context(mission_id=1)
            history_text = "\n".join([f"{h['brain_source']}: {h['command_executed']} -> {h['status']}" for h in history_rows[-5:]])

            # 2. STRATEGIC REASONING (DeepSeek)
            # It analyzes the history and provides a high-level plan.
            strategy_prompt = f"Target: {self.target}\nPast Actions:\n{history_text}\nTask: Plan the next move to achieve 90% recon."
            strategy_output = self.reasoner(f"### Instruction: {strategy_prompt}\n### Thinking:", max_tokens=256, stop=["###"])
            strategy = strategy_output['choices'][0]['text'].strip()

            # 3. TACTICAL EXECUTION (DeepHat)
            # It takes the strategy and turns it into a real Linux command.
            tactical_prompt = f"Strategy: {strategy}\nProvide the exact Kali command to execute."
            cmd_output = self.executor(f"### Strategy: {tactical_prompt}\n### Command: ", max_tokens=128, stop=["\n"])
            generated_cmd = cmd_output['choices'][0]['text'].strip()

            # 4. NEURAL SHIELD VALIDATION
            is_safe, final_cmd = self.shield.validate_command(generated_cmd, self.load_manifest())
            
            if is_safe:
                # 5. EXECUTION VIA KALI BRIDGE
                print(f"\n[>] {strategy}")
                print(f"[>] EXECUTING: {final_cmd}")
                
                result = await self.execute_on_kali(final_cmd)
                
                # 6. SANITIZATION & LOGGING
                safe_output = self.shield.sanitize_output(result['stdout'])
                self.vault.log_terminal_action(1, "DeepNightmare", final_cmd, safe_output, "Success")
                
                # 7. MOTIVATION CHECK
                if "success" in safe_output.lower() or "open" in safe_output.lower():
                    last_success_time = time.time()
                    print(self.motivator.get_status_message(last_success_time, success_found=True))
                else:
                    print(self.motivator.get_status_message(last_success_time))

            await asyncio.sleep(2) # Prevent CPU throttling

    async def execute_on_kali(self, command):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(KALI_BRIDGE_URL, json={"command": command, "mission_id": 1}, timeout=300) as resp:
                    return await resp.json()
            except Exception as e:
                return {"stdout": f"Error connecting to Kali Bridge: {str(e)}", "stderr": ""}

    def load_manifest(self):
        with open('tool_manifest.json', 'r') as f:
            return json.load(f)

if __name__ == "__main__":
    target = input("Enter target URL/Domain: ")
    apex = DeepNightmareApex(target)
    asyncio.run(apex.run_mission())
