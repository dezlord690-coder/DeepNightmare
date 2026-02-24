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
BRAIN_MODEL = "qwen2.5-coder:0.5b" 
KALI_BRIDGE_URL = "http://127.0.0.1:9001/exec"

class DeepNightmareApex:
    def __init__(self, target):
        self.target = target
        self.vault = MissionVault()
        self.shield = NeuralShield()
        self.motivator = MotivationEngine()
        self.mission_id = None
        self.is_running = True
        self.last_success_time = datetime.datetime.now()

    async def initialize_mission(self):
        """Sets up the mission and the 100-question intel tracking."""
        try:
            with self.vault.conn:
                cursor = self.vault.conn.execute(
                    "INSERT INTO missions (target_url, start_date, current_phase) VALUES (?, ?, ?)",
                    (self.target, datetime.datetime.now(), 1)
                )
                self.mission_id = cursor.lastrowid
            print(f"[+] MISSION {self.mission_id} START: {self.target}")
        except Exception:
            cursor = self.vault.conn.execute("SELECT id FROM missions WHERE target_url = ?", (self.target,))
            self.mission_id = cursor.fetchone()[0]
            print(f"[*] RESUMING MISSION {self.mission_id}")

    async def ask_qwen(self, prompt, system_instruction):
        """Direct communication with the Qwen2.5-Coder brain."""
        payload = {
            "model": BRAIN_MODEL,
            "prompt": f"{system_instruction}\n\nContext: {prompt}",
            "stream": False,
            "options": {"temperature": 0.2, "num_thread": 4}
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OLLAMA_API_URL, json=payload, timeout=60) as resp:
                    data = await resp.json()
                    return data.get('response', '').strip()
            except Exception as e:
                return f"Error: {str(e)}"

    async def run_mission(self):
        await self.initialize_mission()
        
        while self.is_running:
            # 1. ANALYZE CURRENT STATE (Vault Check)
            stats = self.vault.get_recon_stats(self.target)
            recon_pct = stats.get('recon_pct', 0)

            # PHASE LOGIC: Recon -> Vuln -> Exploit
            if recon_pct < 90:
                goal = f"PHASE 1 (RECON): Identify WAF, DNS, and hosting. Current progress: {recon_pct}%."
                instruction = "You are a lead recon specialist. Suggest the next terminal command."
            else:
                goal = f"PHASE 2 (VULNERABILITY): Recon is at {recon_pct}%. Search for RCE or Request Smuggling."
                instruction = "You are an exploitation expert. Suggest a high-impact scan command."

            # 2. GENERATE COMMAND (Single Brain, Two-Step logic)
            print(f"[*] Brain is thinking (Recon: {recon_pct}%)...", end="\r")
            strategy = await self.ask_qwen(goal, "Provide a brief strategy.")
            raw_command = await self.ask_qwen(f"Strategy: {strategy}", "Output ONLY the bash command.")

            # 3. NEURAL SHIELD VALIDATION
            is_safe, final_cmd = self.shield.validate_command(raw_command, self.load_manifest())

            if is_safe:
                print(f"\n[PHASE {self.vault.get_phase(self.target)}] Strategy: {strategy[:80]}...")
                print(f"[>] EXECUTING: {final_cmd}")
                
                # 4. ASYNC EXECUTION (Multi-Terminal Flow)
                asyncio.create_task(self.execute_task(final_cmd, strategy))
            else:
                print(f"\n[!] SHIELD BLOCKED: {raw_command}")

            # 5. MOTIVATION / STAGNATION CHECK
            await self.check_mission_status()

            await asyncio.sleep(15) # Prevent CPU lockup

    async def execute_task(self, cmd, strategy):
        """Asynchronously runs command and updates database."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(KALI_BRIDGE_URL, json={"command": cmd, "mission_id": self.mission_id}, timeout=300) as resp:
                    result = await resp.json()
                    stdout = result.get('stdout', '')
                    
                    # Log to Vault for Brain to read next cycle
                    status = "Success" if "open" in stdout.lower() or "found" in stdout.lower() else "Finished"
                    if status == "Success":
                        self.last_success_time = datetime.datetime.now()

                    self.vault.log_terminal_action(self.mission_id, "Qwen-Brain", cmd, self.shield.sanitize_output(stdout), status)
                    print(f"\n[✔] TASK COMPLETE: {cmd[:20]}... Logged to Vault.")
            except Exception as e:
                print(f"[!] Bridge Error: {e}")

    async def check_mission_status(self):
        """Handles the 20-minute stagnation logic and 'BOOM' messages."""
        msg = self.motivator.get_status_message(self.last_success_time)
        print(f"[STATUS] {msg}")

    def load_manifest(self):
        try:
            with open('tool_manifest.json', 'r') as f: return json.load(f)
        except: return {"approved_tools": ["nmap", "sqlmap", "dirsearch", "wafw00f", "nikto", "curl"]}

if __name__ == "__main__":
    target = input("Enter target URL: ")
    apex = DeepNightmareApex(target)
    try:
        asyncio.run(apex.run_mission())
    except KeyboardInterrupt:
        print("\n[!] Shutting down DeepNightmare...")
