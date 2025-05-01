import cv2
import numpy as np
from PIL import Image
import time
import os
import threading

class EmotionDetector:
    """
    Computer vision-based emotion detection for FlexiBuddy.
    Detects basic emotions from webcam input to adapt to the child's emotional state.
    """
    def __init__(self):
        self.emotions = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'confused']
        self.current_emotion = 'neutral'
        self.confidence = 0.0
        self.last_detection_time = 0
        self.detection_interval = 5  # seconds between detections
        self.is_running = False
        self.detection_thread = None
        
        # Load face detection model
        self.face_cascade = None
        try:
            # Try to load OpenCV's built-in face detector
            model_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(model_path):
                self.face_cascade = cv2.CascadeClassifier(model_path)
                print("Loaded face detection model")
            else:
                print(f"Face detection model not found at {model_path}")
        except Exception as e:
            print(f"Error loading face detection model: {e}")
    
    def start_detection(self, callback=None):
        """
        Starts emotion detection in a background thread
        
        Args:
            callback (function): Optional callback function to call when emotion changes
        """
        if self.is_running:
            print("Emotion detection is already running")
            return False
        
        if not self.face_cascade:
            print("Face detection model not loaded, cannot start detection")
            return False
        
        self.is_running = True
        self.detection_thread = threading.Thread(
            target=self._detection_loop,
            args=(callback,),
            daemon=True
        )
        self.detection_thread.start()
        return True
    
    def stop_detection(self):
        """
        Stops the emotion detection thread
        """
        self.is_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=1.0)
            self.detection_thread = None
    
    def _detection_loop(self, callback=None):
        """
        Main detection loop that runs in a background thread
        """
        try:
            # Try to open the webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Could not open webcam")
                self.is_running = False
                return
            
            while self.is_running:
                # Check if it's time for a new detection
                current_time = time.time()
                if current_time - self.last_detection_time >= self.detection_interval:
                    # Capture frame
                    ret, frame = cap.read()
                    if not ret:
                        print("Failed to capture frame from webcam")
                        break
                    
                    # Detect emotion
                    emotion, confidence = self._detect_emotion(frame)
                    
                    # Update state if emotion changed
                    if emotion != self.current_emotion or abs(confidence - self.confidence) > 0.2:
                        old_emotion = self.current_emotion
                        self.current_emotion = emotion
                        self.confidence = confidence
                        
                        # Call callback if provided
                        if callback and old_emotion != emotion:
                            callback(emotion, confidence)
                    
                    self.last_detection_time = current_time
                
                # Sleep to avoid high CPU usage
                time.sleep(0.1)
            
            # Release webcam
            cap.release()
            
        except Exception as e:
            print(f"Error in emotion detection loop: {e}")
            self.is_running = False
    
    def _detect_emotion(self, frame):
        """
        Detects emotion from a video frame
        
        Args:
            frame: OpenCV video frame
            
        Returns:
            tuple: (emotion, confidence)
        """
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # If no faces detected, return current emotion with low confidence
            if len(faces) == 0:
                return (self.current_emotion, 0.1)
            
            # Process the largest face
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_face
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # In a real implementation, we would use a trained emotion classifier here
            # For this example, we'll use a simple heuristic based on face position
            # This is just a placeholder - in a real app, use a proper ML model
            
            # Calculate simple features
            avg_intensity = np.mean(face_roi)
            variance = np.var(face_roi)
            
            # Simple heuristic (this is just for demonstration)
            if variance > 2000:  # High variance might indicate expressive face
                if avg_intensity > 130:  # Brighter face might indicate happiness
                    return ('happy', 0.6)
                else:  # Darker face might indicate negative emotion
                    return ('sad', 0.5)
            else:  # Low variance might indicate neutral expression
                return ('neutral', 0.7)
            
        except Exception as e:
            print(f"Error detecting emotion: {e}")
            return (self.current_emotion, 0.1)
    
    def get_current_emotion(self):
        """
        Returns the current detected emotion
        
        Returns:
            tuple: (emotion, confidence)
        """
        return (self.current_emotion, self.confidence)
    
    def capture_single_emotion(self):
        """
        Captures a single frame and detects emotion
        
        Returns:
            tuple: (emotion, confidence)
        """
        try:
            # Try to open the webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Could not open webcam")
                return (self.current_emotion, 0.1)
            
            # Capture frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                print("Failed to capture frame from webcam")
                return (self.current_emotion, 0.1)
            
            # Detect emotion
            emotion, confidence = self._detect_emotion(frame)
            
            # Update current emotion
            self.current_emotion = emotion
            self.confidence = confidence
            
            return (emotion, confidence)
            
        except Exception as e:
            print(f"Error capturing emotion: {e}")
            return (self.current_emotion, 0.1)
    
    def get_emotion_feedback(self, emotion=None, confidence=None):
        """
        Generates feedback based on detected emotion
        
        Args:
            emotion (str): Emotion to generate feedback for (uses current if None)
            confidence (float): Confidence in the emotion detection
            
        Returns:
            dict: Feedback information
        """
        if emotion is None:
            emotion, confidence = self.current_emotion, self.confidence
        
        feedback = {
            'emotion': emotion,
            'confidence': confidence,
            'timestamp': time.time(),
            'suggestions': []
        }
        
        # Generate suggestions based on emotion
        if emotion == 'happy':
            feedback['suggestions'] = [
                "Child is engaged and happy. Continue current activity.",
                "Good time to introduce new concepts while maintaining enthusiasm."
            ]
        elif emotion == 'sad':
            feedback['suggestions'] = [
                "Child may need encouragement or a change of activity.",
                "Consider a more interactive or rewarding activity.",
                "Offer positive reinforcement for participation."
            ]
        elif emotion == 'angry' or emotion == 'frustrated':
            feedback['suggestions'] = [
                "Child may need a calming activity or break.",
                "Consider simplifying the current task.",
                "Offer a mindfulness exercise to reduce frustration."
            ]
        elif emotion == 'surprised':
            feedback['suggestions'] = [
                "Child is showing interest. Good moment for learning.",
                "Build on this curiosity with related content."
            ]
        elif emotion == 'confused':
            feedback['suggestions'] = [
                "Child may need clearer instructions or examples.",
                "Break down the current task into smaller steps.",
                "Provide visual aids to support understanding."
            ]
        else:  # neutral
            feedback['suggestions'] = [
                "Child appears neutral. Monitor engagement level.",
                "Consider introducing more stimulating content if appropriate."
            ]
        
        return feedback