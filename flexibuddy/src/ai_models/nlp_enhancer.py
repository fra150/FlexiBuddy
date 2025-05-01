import numpy as np
import re
import random
from datetime import datetime

class NLPEnhancer:
    """
    Enhances the NLPProcessor with additional capabilities for personalized responses
    and learning from user interactions.
    """
    def __init__(self, nlp_processor=None):
        self.nlp_processor = nlp_processor
        self.interaction_history = []
        self.learning_rate = 0.1  # Rate at which the system adapts to user preferences
        self.max_history_size = 50  # Maximum number of interactions to store
        
        # Personalized response templates based on user emotion and context
        self.personalized_responses = {
            'happy': [
                "I'm so glad you're happy! Let's keep having fun!",
                "Your happiness makes me happy too! What would you like to do next?",
                "I love seeing you smile! You're doing great!"
            ],
            'sad': [
                "I notice you might be feeling a bit sad. Would you like to try a fun activity?",
                "It's okay to feel sad sometimes. I'm here to help you feel better.",
                "Let's do something that might cheer you up! How about a game?"
            ],
            'frustrated': [
                "I can see this might be frustrating. Let's try something different.",
                "It's okay to take a break if you're feeling frustrated.",
                "Everyone gets stuck sometimes. Let's try a different approach."
            ],
            'bored': [
                "Feeling bored? I have lots of exciting activities we can try!",
                "Let's find something more interesting for you!",
                "I know just the thing to make learning fun again!"
            ],
            'confused': [
                "I can explain that differently if you're confused.",
                "Let's break this down into simpler steps.",
                "It's okay to be confused - that's how we learn new things!"
            ]
        }
        
        # Educational encouragement phrases
        self.educational_encouragements = [
            "You're learning so much today!",
            "I can see how smart you are!",
            "You're making great progress!",
            "Your brain is growing stronger with each activity!",
            "You're a fantastic learner!"
        ]
    
    def process_with_context(self, text, current_emotion="neutral", current_activity="unknown", age_level=6):
        """
        Process user input with contextual awareness of emotion and current activity
        
        Args:
            text (str): User's text input
            current_emotion (str): User's current detected emotion
            current_activity (str): Current activity being performed
            age_level (int): User's age/comprehension level
            
        Returns:
            dict: Enhanced processing results
        """
        # Use base NLP processor if available
        if self.nlp_processor:
            base_result = self.nlp_processor.process_input(text, age_level)
            intent = base_result['intent']
            confidence = base_result['confidence']
        else:
            # Simple fallback if NLP processor not available
            intent = "unknown"
            confidence = 0.0
            base_result = {
                'original_text': text,
                'intent': intent,
                'confidence': confidence,
                'response': "",
                'original_response': ""
            }
        
        # Generate enhanced response based on emotion and context
        enhanced_response = self._generate_enhanced_response(
            intent, confidence, current_emotion, current_activity
        )
        
        # Record this interaction
        self._record_interaction({
            'text': text,
            'intent': intent,
            'emotion': current_emotion,
            'activity': current_activity,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Combine base result with enhancements
        result = base_result.copy()
        result['enhanced_response'] = enhanced_response
        result['current_emotion'] = current_emotion
        result['current_activity'] = current_activity
        
        return result
    
    def _generate_enhanced_response(self, intent, confidence, emotion, activity):
        """
        Generates an emotionally appropriate response based on context
        
        Args:
            intent (str): Detected intent
            confidence (float): Confidence in the intent
            emotion (str): User's current emotion
            activity (str): Current activity
            
        Returns:
            str: Enhanced response
        """
        # Map emotion to response category
        if emotion in ['sad', 'upset']:
            response_category = 'sad'
        elif emotion in ['angry', 'frustrated']:
            response_category = 'frustrated'
        elif emotion in ['happy', 'excited']:
            response_category = 'happy'
        elif emotion in ['confused', 'puzzled']:
            response_category = 'confused'
        elif emotion in ['bored', 'disinterested']:
            response_category = 'bored'
        else:
            response_category = 'happy'  # Default to positive responses
        
        # Get appropriate responses for the emotion
        if response_category in self.personalized_responses:
            responses = self.personalized_responses[response_category]
            base_response = random.choice(responses)
        else:
            base_response = "I'm here to help you learn and have fun!"
        
        # Add educational encouragement occasionally (30% chance)
        if random.random() < 0.3:
            encouragement = random.choice(self.educational_encouragements)
            base_response = f"{base_response} {encouragement}"
        
        # Add activity-specific content if confidence is high
        if confidence > 0.5 and activity != "unknown":
            activity_name = activity.replace('_', ' ').title()
            if intent == 'confused':
                base_response += f" Let me explain this {activity_name} better."
            elif intent == 'bored':
                base_response += f" Would you like to try a different activity instead of {activity_name}?"
        
        return base_response
    
    def _record_interaction(self, interaction_data):
        """
        Records an interaction for learning and adaptation
        
        Args:
            interaction_data (dict): Data about the interaction
        """
        self.interaction_history.append(interaction_data)
        
        # Trim history if it gets too long
        if len(self.interaction_history) > self.max_history_size:
            self.interaction_history = self.interaction_history[-self.max_history_size:]
    
    def get_learning_insights(self):
        """
        Analyzes interaction history to generate insights about learning patterns
        
        Returns:
            dict: Learning insights
        """
        if not self.interaction_history:
            return {"message": "Not enough interaction data to generate insights."}
        
        # Count intents
        intent_counts = {}
        for interaction in self.interaction_history:
            intent = interaction['intent']
            if intent not in intent_counts:
                intent_counts[intent] = 0
            intent_counts[intent] += 1
        
        # Count emotions
        emotion_counts = {}
        for interaction in self.interaction_history:
            emotion = interaction['emotion']
            if emotion not in emotion_counts:
                emotion_counts[emotion] = 0
            emotion_counts[emotion] += 1
        
        # Analyze activity-emotion correlations
        activity_emotions = {}
        for interaction in self.interaction_history:
            activity = interaction['activity']
            emotion = interaction['emotion']
            
            if activity not in activity_emotions:
                activity_emotions[activity] = {}
            
            if emotion not in activity_emotions[activity]:
                activity_emotions[activity][emotion] = 0
            
            activity_emotions[activity][emotion] += 1
        
        # Generate insights
        insights = {
            "common_intents": sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            "emotional_distribution": emotion_counts,
            "activity_emotions": activity_emotions,
            "interaction_count": len(self.interaction_history)
        }
        
        return insights
    
    def add_personalized_response(self, emotion, response):
        """
        Adds a new personalized response for a specific emotion
        
        Args:
            emotion (str): Emotion category
            response (str): Response template to add
        """
        if emotion not in self.personalized_responses:
            self.personalized_responses[emotion] = []
        
        self.personalized_responses[emotion].append(response)