import random
import time
import pandas as pd
from src.utils.config import APP_CONFIG
from src.ai_models.recommendation_engine import RecommendationEngine

class ActivitySwitcher:
    """
    Manages activity switching based on user preferences,
    attention span and frustration level.
    Uses AI recommendation engine to personalize activity selection.
    """
    def __init__(self, data_logger=None):
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
        
        # Initialize AI recommendation engine
        self.data_logger = data_logger
        self.recommendation_engine = RecommendationEngine(data_logger)
        self.use_ai_recommendations = APP_CONFIG.get("use_ai_recommendations", True)
    
    def get_next_activity(self, current_activity=None, reason="timeout", frustration_level=0):
        """
        Determines the next activity based on various factors:
        - Current activity (to avoid repetition)
        - Reason for change (timeout, boredom, voice command)
        - User's frustration level
        - User's historical preferences
        - AI-driven recommendations based on engagement patterns
        
        Args:
            current_activity (str): Currently running activity
            reason (str): Reason for change ('timeout', 'boredom', 'voice_command')
            frustration_level (int): User's frustration level (0-10)
            
        Returns:
            str: Name of the next activity to execute
        """
        # Try to get AI recommendation if enabled
        if self.use_ai_recommendations and self.recommendation_engine:
            # Update recommendation engine with latest data if data logger is available
            if self.data_logger:
                # Load data from data logger's CSV files
                try:
                    activity_data = pd.read_csv(self.data_logger.activity_log) if hasattr(self.data_logger, 'activity_log') else None
                    attention_data = pd.read_csv(self.data_logger.attention_log) if hasattr(self.data_logger, 'attention_log') else None
                    frustration_data = pd.read_csv(self.data_logger.frustration_log) if hasattr(self.data_logger, 'frustration_log') else None
                    
                    # Update recommendation engine with latest data
                    self.recommendation_engine.update_profile(
                        activity_data=activity_data,
                        attention_data=attention_data,
                        frustration_data=frustration_data
                    )
                except Exception as e:
                    print(f"Error updating recommendation engine: {e}")
            
            # Get AI recommendation
            ai_recommendation = self.recommendation_engine.get_recommended_activity(
                current_activity=current_activity,
                reason=reason,
                frustration_level=frustration_level
            )
            
            # Use AI recommendation if available
            if ai_recommendation:
                print(f"AI recommended activity: {ai_recommendation}")
                self.activity_history.append(ai_recommendation)
                if len(self.activity_history) > self.max_history_size * 2:
                    self.activity_history = self.activity_history[-self.max_history_size:]
                return ai_recommendation
        
        # Fall back to rule-based selection if AI recommendation is not available
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