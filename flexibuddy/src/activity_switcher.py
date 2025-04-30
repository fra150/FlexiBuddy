import random
import time
from src.utils.config import APP_CONFIG

class ActivitySwitcher:
    """
    Manages activity switching based on user preferences,
    attention span and frustration level.
    """
    def __init__(self):
        # I define the list of available activities
        self.activities = [
            "memory",
            "quiz", 
            "disegno",
            "mindfulness"
        ]
        
        # I load configurations and timing settings
        self.max_activity_duration = APP_CONFIG.get("max_activity_duration", 180)  # 3 minutes default
        self.min_activity_duration = APP_CONFIG.get("min_activity_duration", 60)   # 1 minute default
        
        # I initialize activity history to avoid immediate repetitions
        self.activity_history = []
        self.max_history_size = 3
        
        # I initialize user preferences (will be populated with usage)
        self.user_preferences = {}
    
    def get_next_activity(self, current_activity=None, reason="timeout", frustration_level=0):
        """
        Determines the next activity based on various factors:
        - Current activity (to avoid repetition)
        - Reason for change (timeout, boredom, voice command)
        - User's frustration level
        - User's historical preferences
        
        Args:
            current_activity (str): Currently running activity
            reason (str): Reason for change ('timeout', 'boredom', 'voice_command')
            frustration_level (int): User's frustration level (0-10)
            
        Returns:
            str: Name of the next activity to execute
        """
        # I filter out the current activity
        available_activities = [a for a in self.activities if a != current_activity]
        
        # I further filter based on recent history to avoid repetitions
        if len(self.activity_history) > 0:
            recent_activities = self.activity_history[-min(len(self.activity_history), self.max_history_size):]
            preferred_activities = [a for a in available_activities if a not in recent_activities]
            
            # I use non-recent activities if available
            if preferred_activities:
                available_activities = preferred_activities
        
        # I prioritize more engaging activities if user is bored or frustrated
        if reason == "boredom" or frustration_level > 5:
            engaging_activities = ["memory", "disegno"]  # I define which are more engaging
            engaging_options = [a for a in available_activities if a in engaging_activities]
            
            if engaging_options:
                available_activities = engaging_options
        
        # I prioritize calming activities if user is highly frustrated
        if frustration_level > 8:
            calming_activities = ["mindfulness"]
            calming_options = [a for a in available_activities if a in calming_activities]
            
            if calming_options:
                return random.choice(calming_options)
        
        # I randomly select from available activities
        next_activity = random.choice(available_activities)
        
        # I update the activity history
        self.activity_history.append(next_activity)
        if len(self.activity_history) > self.max_history_size * 2:
            self.activity_history = self.activity_history[-self.max_history_size:]
        
        return next_activity
    
    def update_user_preference(self, activity, engagement_score):
        """
        Updates user preferences based on engagement score
        
        Args:
            activity (str): Activity name
            engagement_score (float): Engagement score (0-10)
        """
        if activity not in self.user_preferences:
            self.user_preferences[activity] = []
        
        # I add the new score
        self.user_preferences[activity].append(engagement_score)
        
        # I keep only the last 5 scores
        if len(self.user_preferences[activity]) > 5:
            self.user_preferences[activity] = self.user_preferences[activity][-5:]
    
    def get_most_engaging_activities(self, limit=2):
        """
        Returns the most engaging activities based on collected data
        Args:
            limit (int): Number of activities to return 
        Returns:
            list: List of most engaging activities
        """
        if not self.user_preferences:
            return random.sample(self.activities, min(limit, len(self.activities)))
        
        # I calculate average scores for each activity
        avg_scores = {}
        for activity, scores in self.user_preferences.items():
            if scores:
                avg_scores[activity] = sum(scores) / len(scores)
        sorted_activities = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
        return [activity for activity, _ in sorted_activities[:limit]]