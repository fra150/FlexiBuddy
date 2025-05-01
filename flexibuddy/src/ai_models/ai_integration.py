import pandas as pd
import numpy as np
from datetime import datetime
import time
import random

class AIIntegration:
    """
    Integrates all AI components of FlexiBuddy into a unified interface.
    Coordinates between NLPProcessor, EmotionDetector, and RecommendationEngine
    to provide intelligent responses and adaptations to the user's needs.
    """
    def __init__(self, nlp_processor=None, emotion_detector=None, recommendation_engine=None, data_logger=None):
        self.nlp_processor = nlp_processor
        self.emotion_detector = emotion_detector
        self.recommendation_engine = recommendation_engine
        self.data_logger = data_logger
        
        # Initialize state
        self.last_emotion_check = 0
        self.emotion_check_interval = 10  # seconds between emotion checks
        self.current_emotion = "neutral"
        self.emotion_confidence = 0.0
        self.ai_insights = ""
        self.last_insight_time = 0
        self.insight_interval = 60  # seconds between generating new insights
        
        # Adaptive learning parameters
        self.adaptation_level = 0.5  # How quickly the system adapts (0-1)
        self.difficulty_adjustments = {}
        
        # Educational insights templates
        self.insight_templates = {
            "engagement": [
                "I notice {name} is very engaged with {activity}. Great choice!",
                "{name} seems to really enjoy {activity}. This is helping build skills in {skill}.",
                "The current activity is a great match for {name}'s learning style!"
            ],
            "frustration": [
                "{name} might need a bit more support with {activity}.",
                "I've noticed some frustration with {activity}. Maybe we could try {alternative}?",
                "A short break might help {name} reset before continuing."
            ],
            "progress": [
                "{name} is making excellent progress in {skill}!",
                "I've noticed improvement in {name}'s {skill} skills.",
                "The practice with {activity} is really paying off!"
            ],
            "suggestion": [
                "Based on {name}'s preferences, {activity} might be a good next activity.",
                "To build on current progress, {activity} would be beneficial.",
                "For variety, {name} might enjoy trying {activity} next."
            ]
        }
    
    def process_input(self, text, current_activity="unknown", user_name="Friend"):
        """
        Process user text input using NLP and generate appropriate response
        
        Args:
            text (str): User's text input
            current_activity (str): Current activity being performed
            user_name (str): User's name for personalization
            
        Returns:
            dict: Processing results including response
        """
        if not self.nlp_processor:
            return {"response": "I'm here to help you learn and have fun!"}
        
        # Check emotion if available and time interval passed
        self._update_emotion_if_needed()
        
        # Process text with NLP processor
        result = self.nlp_processor.process_input(text)
        
        # Enhance response with emotion awareness if available
        if hasattr(self.nlp_processor, 'process_with_context'):
            enhanced_result = self.nlp_processor.process_with_context(
                text, 
                current_emotion=self.current_emotion,
                current_activity=current_activity
            )
            response = enhanced_result.get('enhanced_response', result['response'])
        else:
            response = result['response']
        
        # Personalize with user's name
        response = response.replace("{name}", user_name)
        
        # Log the interaction if data logger is available
        if self.data_logger:
            try:
                self.data_logger.log_interaction({
                    "text": text,
                    "intent": result.get('intent', 'unknown'),
                    "emotion": self.current_emotion,
                    "activity": current_activity,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                print(f"Error logging interaction: {e}")
        
        return {
            "response": response,
            "intent": result.get('intent', 'unknown'),
            "confidence": result.get('confidence', 0.0),
            "emotion": self.current_emotion
        }
    
    def get_activity_recommendation(self, current_activity=None, reason="timeout", frustration_level=0):
        """
        Get AI-powered activity recommendation
        
        Args:
            current_activity (str): Currently running activity
            reason (str): Reason for change ('timeout', 'boredom', 'voice_command')
            frustration_level (int): User's frustration level (0-10)
            
        Returns:
            str: Recommended activity name or None if no recommendation
        """
        if not self.recommendation_engine:
            return None
        
        # Update recommendation engine with latest data if data logger is available
        if self.data_logger:
            try:
                # Load data from data logger's CSV files
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
        
        # Get recommendation
        recommendation = self.recommendation_engine.get_recommended_activity(
            current_activity=current_activity,
            reason=reason,
            frustration_level=frustration_level
        )
        
        return recommendation
    
    def detect_emotion(self):
        """
        Detect user's emotion using the emotion detector
        
        Returns:
            tuple: (emotion, confidence)
        """
        if not self.emotion_detector:
            return ("neutral", 0.0)
        
        try:
            # Capture single emotion
            emotion, confidence = self.emotion_detector.capture_single_emotion()
            self.current_emotion = emotion
            self.emotion_confidence = confidence
            self.last_emotion_check = time.time()
            
            return (emotion, confidence)
        except Exception as e:
            print(f"Error detecting emotion: {e}")
            return ("neutral", 0.0)
    
    def _update_emotion_if_needed(self):
        """
        Updates the current emotion if enough time has passed since last check
        """
        current_time = time.time()
        if current_time - self.last_emotion_check >= self.emotion_check_interval:
            if self.emotion_detector:
                self.detect_emotion()
    
    def generate_insight(self, user_name="Friend", current_activity="unknown"):
        """
        Generates an educational insight based on user behavior and current context
        
        Args:
            user_name (str): User's name for personalization
            current_activity (str): Current activity being performed
            
        Returns:
            str: Educational insight
        """
        current_time = time.time()
        
        # Only generate new insights periodically
        if current_time - self.last_insight_time < self.insight_interval:
            return self.ai_insights
        
        # Get insights from recommendation engine if available
        if self.recommendation_engine:
            try:
                insights = self.recommendation_engine.get_insights()
                
                if insights and insights.get("preferred_activities"):
                    # Choose insight type based on context
                    if self.current_emotion in ["happy", "excited"]:
                        insight_type = "engagement"
                    elif self.current_emotion in ["sad", "frustrated", "angry"]:
                        insight_type = "frustration"
                    elif random.random() < 0.7:  # 70% chance for progress insights
                        insight_type = "progress"
                    else:
                        insight_type = "suggestion"
                    
                    # Get template for this insight type
                    templates = self.insight_templates.get(insight_type, [])
                    if templates:
                        template = random.choice(templates)
                        
                        # Fill in template placeholders
                        activity_name = current_activity.replace('_', ' ').title()
                        alternative = random.choice(insights["preferred_activities"]).replace('_', ' ').title() \
                            if insights.get("preferred_activities") else "another activity"
                        
                        # Map activities to skills (simplified)
                        skills = {
                            "memory_game": "memory and concentration",
                            "quiz_game": "knowledge and critical thinking",
                            "drawing_activity": "creativity and fine motor skills",
                            "mindfulness_break": "emotional regulation"
                        }
                        
                        skill = skills.get(current_activity, "learning")
                        
                        # Format the insight
                        insight = template.format(
                            name=user_name,
                            activity=activity_name,
                            alternative=alternative,
                            skill=skill
                        )
                        
                        self.ai_insights = insight
                        self.last_insight_time = current_time
                        return insight
            except Exception as e:
                print(f"Error generating insight: {e}")
        
        # Fallback insights if recommendation engine fails or isn't available
        fallback_insights = [
            f"{user_name} is doing well with learning through play!",
            f"I notice {user_name} enjoys interactive activities.",
            f"Regular breaks help {user_name} stay focused and learn better.",
            f"Mixing different types of activities helps develop multiple skills."
        ]
        
        self.ai_insights = random.choice(fallback_insights)
        self.last_insight_time = current_time
        return self.ai_insights
    
    def adapt_difficulty(self, activity, success_rate):
        """
        Adapts activity difficulty based on user's success rate
        
        Args:
            activity (str): Activity name
            success_rate (float): Rate of success (0-1)
            
        Returns:
            dict: Difficulty adjustment parameters
        """
        if activity not in self.difficulty_adjustments:
            self.difficulty_adjustments[activity] = 0.5  # Start at medium difficulty
        
        current_difficulty = self.difficulty_adjustments[activity]
        
        # Adjust difficulty based on success rate
        # If success rate is high, increase difficulty
        # If success rate is low, decrease difficulty
        if success_rate > 0.8:  # Very successful
            new_difficulty = current_difficulty + (0.1 * self.adaptation_level)
        elif success_rate < 0.4:  # Struggling
            new_difficulty = current_difficulty - (0.1 * self.adaptation_level)
        else:  # Doing okay
            new_difficulty = current_difficulty
        
        # Ensure difficulty stays within bounds
        new_difficulty = max(0.1, min(0.9, new_difficulty))
        
        # Update stored difficulty
        self.difficulty_adjustments[activity] = new_difficulty
        
        # Convert normalized difficulty (0-1) to activity-specific parameters
        if activity == "memory_game":
            # Higher difficulty means more items to remember
            items_count = int(3 + (new_difficulty * 4))  # 3-7 items
            display_time = max(1.5, 3 - (new_difficulty * 1.5))  # 1.5-3 seconds
            return {"items_count": items_count, "display_time": display_time}
        
        elif activity == "quiz_game":
            # Higher difficulty means more complex questions
            question_level = int(1 + (new_difficulty * 2))  # 1-3 level
            return {"question_level": question_level}
        
        elif activity == "drawing_activity":
            # Drawing doesn't have difficulty levels
            return {}
        
        elif activity == "mindfulness_break":
            # Adjust duration based on attention span
            duration = int(10 + (new_difficulty * 20))  # 10-30 seconds
            return {"duration": duration}
        
        return {"difficulty": new_difficulty}