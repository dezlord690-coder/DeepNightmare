import random
import time
from datetime import datetime

class MotivationEngine:
    def __init__(self):
        # Categories for the 500 messages
        self.messages = {
            "success": [
                "BOOM 💥 We hit it! Data is flowing into the vault.",
                "Target wall breached. Let's pivot and keep the momentum.",
                "Perfect execution. That's how a pro handles it.",
                "Access confirmed. The perimeter is ours. Let's go deeper."
            ],
            "stagnant": [
                "Things are quiet... too quiet. Re-check the headers.",
                "No success in 20 mins. Let's be more precise and hit it!",
                "Stalling detected. Rotate payloads or increase power.",
                "Don't give up! We are going to succeed. Try a different angle."
            ],
            "encouragement": [
                "That was a hard one, but let's keep the fight.",
                "We dribbled past the first layer. Don't stop now.",
                "Let's be more effective this time. Precision over noise.",
                "Kill it! The objective is within reach."
            ]
        }

    def get_status_message(self, last_update_time, success_found=False):
        """
        Logic to determine which message to send to the AI Brain.
        """
        current_time = time.time()
        time_diff = (current_time - last_update_time) / 60  # in minutes

        if success_found:
            return random.choice(self.messages["success"])
        
        if time_diff >= 20:
            return random.choice(self.messages["stagnant"])
        
        return random.choice(self.messages["encouragement"])

    def broadcast_to_brains(self, message):
        """
        Simulates sending the message to the DeepSeek and DeepHat terminals.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] [MOTIVATION_ENGINE]: {message}"
        print(formatted_msg)
        return formatted_msg

# Example of how the engine integrates with the mission loop:
# last_action = time.time() 
# engine = MotivationEngine()
# print(engine.get_status_message(last_action))
