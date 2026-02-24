import random
import datetime

class MotivationEngine:
    def __init__(self):
        # Professional/Tactical response categories
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
        Determines the motivational trigger based on mission telemetry.
        Standardized to handle datetime objects.
        """
        now = datetime.datetime.now()
        
        # Ensure last_update_time is a datetime object
        if isinstance(last_update_time, (int, float)):
            last_update_time = datetime.datetime.fromtimestamp(last_update_time)

        if success_found:
            return random.choice(self.messages["success"])
        
        # Calculate difference in seconds
        time_diff_seconds = (now - last_update_time).total_seconds()

        # 20 minutes = 1200 seconds
        if time_diff_seconds >= 1200:
            return random.choice(self.messages["stagnant"])
        
        return random.choice(self.messages["encouragement"])

    def broadcast_to_brains(self, message):
        """
        Visual output for the Omni-Dashboard.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] [MOTIVATION_ENGINE]: {message}"
        print(formatted_msg)
        return formatted_msg
