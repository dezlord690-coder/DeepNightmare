import sqlite3
import datetime
import json
import hashlib

class MissionVault:
    def __init__(self, db_path="deepnightmare_vault.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            # Table 1: Primary Target & Phase Management
            self.conn.execute('''CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_url TEXT UNIQUE,
                current_phase INTEGER DEFAULT 1,
                recon_pct INTEGER DEFAULT 0,
                waf_type TEXT,
                hosting_provider TEXT,
                start_date TIMESTAMP,
                last_update TIMESTAMP
            )''')

            # Table 2: The "100 Questions" Intel (JSON Blob for flexibility)
            self.conn.execute('''CREATE TABLE IF NOT EXISTS intel_payloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id INTEGER,
                category TEXT, -- e.g., 'DNS', 'WAF', 'Subdomains'
                data_json TEXT,
                integrity_hash TEXT,
                FOREIGN KEY(mission_id) REFERENCES missions(id)
            )''')

            # Table 3: Multi-Terminal Audit Logs (For AI feedback loop)
            self.conn.execute('''CREATE TABLE IF NOT EXISTS terminal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id INTEGER,
                brain_source TEXT, -- 'DeepSeek' or 'DeepHat'
                command_executed TEXT,
                raw_output TEXT,
                status TEXT, -- 'Success', 'Blocked', 'Pending'
                timestamp TIMESTAMP
            )''')

    # --- PHASE GATE LOGIC ---
    
    def update_recon_progress(self, target_url, waf, provider, percentage):
        """Checks if we hit the 90% mark to move to Phase 2 (Vulnerability)"""
        now = datetime.datetime.now()
        with self.conn:
            self.conn.execute('''UPDATE missions SET 
                waf_type = ?, hosting_provider = ?, recon_pct = ?, last_update = ? 
                WHERE target_url = ?''', (waf, provider, percentage, now, target_url))
        
        if percentage >= 90:
            print(f"[*] GATE SIGNAL: {target_url} reached {percentage}%. Advancing to Phase 2.")
            return True
        return False

    # --- BRAIN SYNC LOGIC ---

    def log_terminal_action(self, mission_id, brain, command, output, status):
        """Stores result so the other AI brain can see it immediately."""
        with self.conn:
            self.conn.execute('''INSERT INTO terminal_logs 
                (mission_id, brain_source, command_executed, raw_output, status, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?)''', 
                (mission_id, brain, command, output, status, datetime.datetime.now()))

    def get_brain_context(self, mission_id):
        """Dumps all history for the AI to analyze past successes/failures."""
        cursor = self.conn.execute("SELECT * FROM terminal_logs WHERE mission_id = ?", (mission_id,))
        return [dict(row) for row in cursor.fetchall()]

# --- INITIALIZATION HELPER ---
def start_new_mission(target):
    vault = MissionVault()
    try:
        with vault.conn:
            vault.conn.execute("INSERT INTO missions (target_url, start_date) VALUES (?, ?)", 
                             (target, datetime.datetime.now()))
        print(f"[+] Mission DeepNightmare initialized for: {target}")
    except sqlite3.IntegrityError:
        print(f"[*] Resuming existing mission for: {target}")
