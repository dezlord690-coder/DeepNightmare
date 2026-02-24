import asyncio
import json
import time
import datetime
import aiohttp
from database_manager import MissionVault
from neural_shield import NeuralShield
from motivation_engine import MotivationEngine

# --- CONFIGURATION ---
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
BRAIN_ANALYST = "deepseek-r1:1.5b"   # Strategy/Logic
BRAIN_EXECUTOR = "qwen2.5-coder:0.5b" # Tactical/Commands
KALI_BRIDGE_URL = "http://127.0.0.1:9001/exec"

class DeepNightmareApex:
    def __init__(self, target):
        self.target = target
        self.vault = MissionVault()
        self.shield = NeuralShield()
        self.motivator = MotivationEngine()
        self.mission_id = None
        self.is_running = True
        self.last_update_time = time.time()

    async def initialize_mission(self):
        """Initializes the mission in the Vault and sets ID."""
        try:
            with self.vault.conn:
                cursor = self.vault.conn.execute(
                    "INSERT INTO missions (target_url, start_date, current_phase) VALUES (?, ?, ?)",
                    (self.target, datetime.datetime.now(), 1)
                )
                self.mission_id = cursor.lastrowid
            print(f"[+] MISSION {self.mission_id} INITIALIZED: {self.target}")
        except Exception:
            cursor = self.vault.conn.execute("SELECT id FROM missions WHERE target_url = ?", (self.target,))
            self.mission_id = cursor.fetchone()[0]
            print(f"[*] RESUMING MISSION {self.mission_id}")

    async def get_dual_brain_logic(self, phase_goal):
        """DeepSeek-R1 analyzes and plans -> DeepHat-V1 writes the command."""
        history = self.vault.get_brain_context(self.mission_id)
        history_str = "\n".join([f"{h['command_executed']} -> {h['status']}" for h in history[-5:]])

        # Step 1: DeepSeek Analysis
        analysis_prompt = f"Target: {self.target}\nPhase Goal: {phase_goal}\nPast Results: {history_str}\nPlan the next precise move."
        print(f"[*] DeepSeek-R1 Analyzing Strategy...", end="\r")
        strategy = await self.ask_brain(BRAIN_ANALYST, analysis_prompt, "### Instruction: Act as a Strategic Reasoner.")

        # Step 2: DeepHat (Qwen) Command Generation
        print(f"[*] DeepHat-V1 Generating Command...", end="\r")
        command_prompt = f"Strategy: {strategy}\nBased on this strategy, provide ONLY the exact Kali Linux command."
        command = await self.ask_brain(BRAIN_EXECUTOR, command_prompt, "### Instruction: Output ONLY the bash string.")
        
        return strategy, command

    async def ask_brain(self, model, prompt, system):
        payload = {"model": model, "prompt": f"{system}\n\n{prompt}", "stream": False, "options": {"num_thread": 4}}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OLLAMA_API_URL, json=payload, timeout=90) as resp:
                    data = await resp.json()
                    res = data.get('response', '')
                    return res.split("</think>")[-1].strip() # Clean DeepSeek tags
            except Exception as e:
                return f"Error: {str(e)}"

    async def run_mission(self):
        await self.initialize_mission()
        
        while self.is_running:
            # 1. READ VAULT FOR PHASE GATE
            stats = self.vault.get_recon_stats(self.target) # Custom method from previous step
            recon_pct = stats.get('recon_pct', 0)

            if recon_pct < 90:
                current_goal = "Achieve 90% recon. Map WAF, DNS, Subdomains, and Hosting."
                phase_label = "PHASE 1: RECON"
            else:
                current_goal = "90% Recon achieved. Identify and exploit vulnerabilities (RCE, SQLi, Smuggling)."
                phase_label = "PHASE 2: EXPLOITATION"

            # 2. GENERATE COMMAND
            strategy, command = await self.get_dual_brain_logic(current_goal)

            # 3. NEURAL SHIELD VALIDATION
            is_safe, final_cmd = self.shield.validate_command(command, self.load_manifest())

            if is_safe:
                print(f"\n[{phase_label}] {strategy[:80]}...")
                print(f"[>] EXECUTING: {final_cmd}")
                
                # 4. ASYNC EXECUTION (Doesn't block the next thought)
                asyncio.create_task(self.execute_task(final_cmd, strategy))
                self.last_update_time = time.time()
            else:
                print(f"[!] SHIELD BLOCKED COMMAND: {command}")

            # 5. MOTIVATION / STAGNATION CHECK
            await self.check_motivation()

            await asyncio.sleep(15) # Cool-down between command generations

    async def execute_task(self, cmd, strategy):
        """Sends to Kali Bridge and updates Vault upon completion."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(KALI_BRIDGE_URL, json={"command": cmd, "mission_id": self.mission_id}, timeout=300) as resp:
                    result = await resp.json()
                    stdout = result.get('stdout', '')
                    # Self-Healing/Recorrection: If output contains WAF info, update Vault
                    status = "Success" if stdout else "Finished"
                    self.vault.log_terminal_action(self.mission_id, "DeepNightmare", cmd, stdout, status)
                    print(f"\n[✔] TASK COMPLETED. Vault Updated.")
            except Exception as e:
                print(f"[!] Bridge Connection Failed: {e}")

    async def check_motivation(self):
        """Checks if 20 minutes have passed without a successful DB update."""
        if (time.time() - self.last_update_time) > 1200: # 1200s = 20min
            msg = self.motivator.get_stagnant_message() # "Increase payload!"
            print(f"\n[!] ALERT: {msg}")
            self.last_update_time = time.time() # Reset timer

    def load_manifest(self):
        try:
            with open('tool_manifest.json', 'r') as f: return json.load(f)
        except: return {}

if __name__ == "__main__":
    target = input("Enter target URL/Domain: ")
    apex = DeepNightmareApex(target)
    try:
        asyncio.run(apex.run_mission())
    except KeyboardInterrupt:
        print("\n[!] Shutting down DeepNightmare Apex...")
