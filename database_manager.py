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
                category TEXT, 
                data_json TEXT,
                integrity_hash TEXT,
                FOREIGN KEY(mission_id) REFERENCES missions(id)
            )''')

            # Table 3: Multi-Terminal Audit Logs
            self.conn.execute('''CREATE TABLE IF NOT EXISTS terminal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id INTEGER,
                brain_source TEXT, 
                command_executed TEXT,
                raw_output TEXT,
                status TEXT, 
                timestamp TIMESTAMP
            )''')

    # --- CORE MISSION GETTERS ---

    def get_recon_stats(self, target_url):
        """Fetches recon data for ares_apex phase gating."""
        cursor = self.conn.execute(
            "SELECT recon_pct, waf_type, hosting_provider, current_phase FROM missions WHERE target_url = ?", 
            (target_url,)
        )
        row = cursor.fetchone()
        return dict(row) if row else {"recon_pct": 0, "waf_type": "None", "hosting_provider": "Unknown", "current_phase": 1}

    def get_phase(self, target_url):
        cursor = self.conn.execute("SELECT current_phase FROM missions WHERE target_url = ?", (target_url,))
        row = cursor.fetchone()
        return row['current_phase'] if row else 1

    # --- INTEL & PROGRESS LOGIC ---

    def update_intel_question(self, mission_id, category, key, value):
        """Updates the flexible JSON intel payloads and secures with hash."""
        with self.conn:
            cursor = self.conn.execute(
                "SELECT data_json FROM intel_payloads WHERE mission_id = ? AND category = ?", 
                (mission_id, category)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row['data_json'])
                data[key] = value
                new_json = json.dumps(data)
                h = hashlib.sha256(new_json.encode()).hexdigest()
                self.conn.execute(
                    "UPDATE intel_payloads SET data_json = ?, integrity_hash = ? WHERE mission_id = ? AND category = ?",
                    (new_json, h, mission_id, category)
                )
            else:
                initial_data = json.dumps({key: value})
                h = hashlib.sha256(initial_data.encode()).hexdigest()
                self.conn.execute(
                    "INSERT INTO intel_payloads (mission_id, category, data_json, integrity_hash) VALUES (?, ?, ?, ?)",
                    (mission_id, category, initial_data, h)
                )

    def update_recon_progress(self, target_url, waf, provider, percentage):
        """Standard progress update. Signals when to advance to Phase 2."""
        now = datetime.datetime.now()
        new_phase = 2 if percentage >= 90 else 1
        with self.conn:
            self.conn.execute('''UPDATE missions SET 
                waf_type = ?, hosting_provider = ?, recon_pct = ?, current_phase = ?, last_update = ? 
                WHERE target_url = ?''', (waf, provider, percentage, new_phase, now, target_url))
        
        if percentage >= 90:
            print(f"[*] GATE SIGNAL: {target_url} reached {percentage}%. Advancing to Phase 2.")
            return True
        return False

    # --- BRAIN SYNC & LOGGING ---

    def log_terminal_action(self, mission_id, brain, command, output, status):
        """Records terminal output so Qwen can read history in the next cycle."""
        with self.conn:
            self.conn.execute('''INSERT INTO terminal_logs 
                (mission_id, brain_source, command_executed, raw_output, status, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?)''', 
                (mission_id, brain, command, output, status, datetime.datetime.now()))

    def get_brain_context(self, mission_id):
        """Retrieves history for the Brain to analyze past successes/failures."""
        cursor = self.conn.execute(
            "SELECT brain_source, command_executed, status FROM terminal_logs WHERE mission_id = ? ORDER BY timestamp DESC LIMIT 5", 
            (mission_id,)
        )
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
