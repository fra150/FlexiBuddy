import re
import string
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class NLPProcessor:
    """
    Natural Language Processing module for FlexiBuddy.
    Provides simplified language processing for children with learning disabilities.
    """
    def __init__(self):
        self.vocabulary = {
            # Basic emotions and states
            'happy': ['happy', 'glad', 'joy', 'smile', 'fun', 'good'],
            'sad': ['sad', 'unhappy', 'cry', 'tears', 'upset', 'bad'],
            'angry': ['angry', 'mad', 'upset', 'annoyed', 'frustrated'],
            'confused': ['confused', 'don\'t understand', 'what', 'how', 'why', 'help'],
            'bored': ['bored', 'boring', 'tired', 'not fun', 'don\'t like'],
            
            # Activity requests
            'change_activity': ['change', 'different', 'another', 'new', 'switch', 'something else'],
            'play_game': ['play', 'game', 'fun', 'start'],
            'draw': ['draw', 'drawing', 'paint', 'color', 'art'],
            'quiz': ['quiz', 'question', 'answer', 'learn'],
            'memory': ['memory', 'remember', 'match', 'find'],
            'mindfulness': ['breathe', 'calm', 'quiet', 'rest', 'relax'],
            
            # Basic commands
            'help': ['help', 'assist', 'support', 'how to'],
            'stop': ['stop', 'end', 'finish', 'exit', 'quit'],
            'repeat': ['repeat', 'again', 'say again', 'what did you say'],
            'slower': ['slow', 'slower', 'too fast', 'wait'],
            
            # Affirmations
            'yes': ['yes', 'yeah', 'yep', 'ok', 'okay', 'sure', 'yup'],
            'no': ['no', 'nope', 'not', 'don\'t', 'never']
        }
        
        # Vectorizer for text similarity
        self.vectorizer = CountVectorizer(lowercase=True, token_pattern=r'\b\w+\b')
        
        # Prepare vectorizer with all vocabulary words
        all_words = [word for synonyms in self.vocabulary.values() for word in synonyms]
        self.vectorizer.fit([' '.join(all_words)])
        
        # Simple responses for common intents
        self.responses = {
            'happy': ["I'm glad you're happy!", "That's wonderful!", "Yay! I'm happy too!"],
            'sad': ["It's okay to feel sad sometimes.", "Would you like to try something fun to feel better?", "I'm here for you."],
            'angry': ["I understand you're feeling upset.", "Let's take a deep breath together.", "Would you like to try a calming activity?"],
            'confused': ["Let me explain that again.", "I'll try to make it simpler.", "What part is confusing?"],
            'bored': ["Let's try something new!", "I have many fun activities we can do!", "Would you like to change the game?"],
            'help': ["I'm here to help! What do you need?", "I can help you with games and activities.", "Tell me what you need help with."],
            'stop': ["Okay, we can stop.", "Let's take a break.", "We can try something else."],
            'repeat': ["I'll say that again.", "Let me repeat that for you.", "Here's what I said..."],
            'slower': ["I'll speak more slowly.", "I'll slow down for you.", "Is this better?"],
            'yes': ["Great!", "Wonderful!", "Let's do it!"],
            'no': ["That's okay.", "No problem.", "We can do something else."]
        }
    
    def simplify_text(self, text, age_level=6):
        """
        Simplifies text based on child's age/comprehension level
        
        Args:
            text (str): Text to simplify
            age_level (int): Target age level for simplification (lower = simpler)
            
        Returns:
            str: Simplified text
        """
        # Remove complex punctuation
        text = re.sub(r'[;:\(\)\[\]\{\}]', '', text)
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        simplified_sentences = []
        for sentence in sentences:
            # For very young children (age 4-6), keep sentences very short
            if age_level <= 6:
                # If sentence is too long, try to break it up
                words = sentence.split()
                if len(words) > 8:
                    # Break into chunks of ~6 words
                    chunks = [words[i:i+6] for i in range(0, len(words), 6)]
                    for chunk in chunks:
                        simplified_sentences.append(' '.join(chunk))
                else:
                    simplified_sentences.append(sentence)
            
            # For older children (age 7-10), simplify but keep more content
            elif age_level <= 10:
                # If sentence is too long, try to break it up
                words = sentence.split()
                if len(words) > 12:
                    # Break into chunks of ~10 words
                    chunks = [words[i:i+10] for i in range(0, len(words), 10)]
                    for chunk in chunks:
                        simplified_sentences.append(' '.join(chunk))
                else:
                    simplified_sentences.append(sentence)
            
            # For older children, keep original sentence
            else:
                simplified_sentences.append(sentence)
        
        # Join sentences with appropriate punctuation
        result = '. '.join(simplified_sentences)
        
        # Ensure proper ending punctuation
        if result and result[-1] not in '.!?':
            result += '.'
        
        return result
    
    def detect_intent(self, text):
        """
        Detects the intent of the user's text
        
        Args:
            text (str): User's text input
            
        Returns:
            tuple: (intent, confidence)
        """
        if not text or not text.strip():
            return ('unknown', 0.0)
        
        # Preprocess text
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        
        # Vectorize the input text
        try:
            text_vector = self.vectorizer.transform([text])
        except Exception:
            # If vectorization fails, fall back to simple word matching
            return self._simple_intent_detection(text)
        
        # Calculate similarity with each intent vocabulary
        similarities = {}
        for intent, words in self.vocabulary.items():
            # Vectorize the intent vocabulary
            intent_text = ' '.join(words)
            intent_vector = self.vectorizer.transform([intent_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(text_vector, intent_vector)[0][0]
            similarities[intent] = similarity
        
        # Get the intent with highest similarity
        best_intent = max(similarities.items(), key=lambda x: x[1])
        
        # Return intent only if similarity is above threshold
        if best_intent[1] > 0.1:  # Low threshold to catch more intents
            return (best_intent[0], best_intent[1])
        else:
            return ('unknown', 0.0)
    
    def _simple_intent_detection(self, text):
        """
        Fallback method for intent detection using simple word matching
        
        Args:
            text (str): User's text input
            
        Returns:
            tuple: (intent, confidence)
        """
        words = text.split()
        matches = {}
        
        for intent, vocabulary in self.vocabulary.items():
            count = sum(1 for word in words if any(v in word for v in vocabulary))
            if count > 0:
                matches[intent] = count / len(words)  # Simple confidence score
        
        if matches:
            best_intent = max(matches.items(), key=lambda x: x[1])
            return (best_intent[0], best_intent[1])
        else:
            return ('unknown', 0.0)
    
    def generate_response(self, intent, confidence=0.0):
        """
        Generates a simple response based on detected intent
        
        Args:
            intent (str): Detected intent
            confidence (float): Confidence score
            
        Returns:
            str: Response text
        """
        if intent in self.responses:
            # Return a random response for the intent
            responses = self.responses[intent]
            return np.random.choice(responses)
        else:
            # Default responses
            default_responses = [
                "I'm not sure I understand. Can you say that differently?",
                "Let's try something fun!",
                "Would you like to play a game?",
                "Tell me more about what you want to do."
            ]
            return np.random.choice(default_responses)
    
    def process_input(self, text, age_level=6):
        """
        Process user input and generate appropriate response
        
        Args:
            text (str): User's text input
            age_level (int): User's age/comprehension level
            
        Returns:
            dict: Processing results including intent and response
        """
        intent, confidence = self.detect_intent(text)
        response = self.generate_response(intent, confidence)
        
        # Simplify the response based on age level
        simplified_response = self.simplify_text(response, age_level)
        
        return {
            'original_text': text,
            'intent': intent,
            'confidence': confidence,
            'response': simplified_response,
            'original_response': response
        }
    
    def add_vocabulary(self, intent, words):
        """
        Adds new vocabulary words for an intent
        
        Args:
            intent (str): Intent name
            words (list): List of words to add
        """
        if intent not in self.vocabulary:
            self.vocabulary[intent] = []
        
        # Add new words
        self.vocabulary[intent].extend([w.lower() for w in words])
        
        # Remove duplicates
        self.vocabulary[intent] = list(set(self.vocabulary[intent]))
        
        # Update vectorizer
        all_words = [word for synonyms in self.vocabulary.values() for word in synonyms]
        self.vectorizer.fit([' '.join(all_words)])
    
    def add_responses(self, intent, responses):
        """
        Adds new response templates for an intent
        
        Args:
            intent (str): Intent name
            responses (list): List of response templates
        """
        if intent not in self.responses:
            self.responses[intent] = []
        
        # Add new responses
        self.responses[intent].extend(responses)
        
        # Remove duplicates
        self.responses[intent] = list(set(self.responses[intent]))