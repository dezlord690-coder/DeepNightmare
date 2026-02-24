import asyncio
import json
import time
import aiohttp
import sqlite3
from database_manager import MissionVault
from neural_shield import NeuralShield

# --- CONFIGURATION ---
MODEL_DEEPSEEK = "deepseek-r1:1.5b"  # The Analyzer
MODEL_DEEPHAT = "qwen2.5-coder:0.5b" # The Executor (Fast)
KALI_BRIDGE_URL = "http://127.0.0.1:9001/exec"

class DeepNightmareApex:
    def __init__(self, target):
        self.target = target
        self.vault = MissionVault()
        self.shield = NeuralShield()
        self.phase = 1 # 1: Recon, 2: Scanning, 3: Exploitation
        self.active_tasks = []

    async def get_brain_consensus(self, prompt):
        """Dual-Brain logic: DeepSeek plans, DeepHat writes the code."""
        # 1. DeepSeek analyzes and plans
        plan = await self.ask_ollama(MODEL_DEEPSEEK, f"Strategic Plan for {self.target}: {prompt}")
        
        # 2. DeepHat converts plan to exact Kali command
        cmd_prompt = f"Plan: {plan}\nProvide ONLY the one-line Kali command to execute."
        command = await self.ask_ollama(MODEL_DEEPHAT, cmd_prompt)
        
        return plan, command

    async def ask_ollama(self, model, prompt):
        payload = {"model": model, "prompt": prompt, "stream": False}
        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:11434/api/generate", json=payload) as resp:
                data = await resp.json()
                return data.get('response', '').strip()

    async def run_mission(self):
        print(f"[!] MISSION START: {self.target} | PHASE: {self.phase}")
        
        while True:
            # Check Phase Completion
            stats = self.vault.get_mission_stats(self.target) 
            if stats['recon_percent'] < 90 and self.phase == 1:
                goal = "Perform deep infrastructure recon (WAF, DNS, Ports)."
            elif self.phase == 1:
                print("[+] Recon 90% Complete. Moving to PHASE 2: Vulnerability Scanning.")
                self.phase = 2
                goal = "Scan for RCE, SQLi, and Request Smuggling based on recon data."
            
            # Get Commands from Dual-Brain
            strategy, cmd = await self.get_brain_consensus(goal)
            
            # Neural Shield Check
            is_safe, final_cmd = self.shield.validate_command(cmd, self.load_manifest())
            
            if is_safe:
                # ASYNC EXECUTION: Don't wait! Open a new task and loop back
                task = asyncio.create_task(self.execute_and_log(final_cmd, strategy))
                self.active_tasks.append(task)
                
                print(f"[>] NEW TASK STARTED: {final_cmd}")
            
            # Motivation / Success Check
            await self.check_success_messages()
            
            # CPU Breath - 10s wait before generating next command
            await asyncio.sleep(10)

    async def execute_and_log(self, cmd, strategy):
        """Runs in background, updates DB when done."""
        async with aiohttp.ClientSession() as session:
            async with session.post(KALI_BRIDGE_URL, json={"command": cmd}) as resp:
                result = await resp.json()
                # Log success/fail to SQLite
                self.vault.update_history(self.target, cmd, result['stdout'], strategy)
                print(f"\n[✔] TASK FINISHED: {cmd[:30]}... Result logged to Vault.")

    def load_manifest(self):
        with open('tool_manifest.json', 'r') as f: return json.load(f)

    async def check_success_messages(self):
        # Implementation of your 500 custom messages based on DB updates
        last_log = self.vault.get_last_entry()
        if "success" in last_log.lower():
            print("💥 BOOM! We hit it. Let's keep the fight!")

if __name__ == "__main__":
    target = input("Enter Target: ")
    apex = DeepNightmareApex(target)
    asyncio.run(apex.run_mission())
