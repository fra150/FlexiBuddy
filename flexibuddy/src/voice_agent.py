import os
import subprocess
import threading
import time
import tempfile
import wave
import numpy as np
import pyaudio
import whisper
from TTS.api import TTS
from src.utils.config import APP_CONFIG
from src.ai_models.nlp_processor import NLPProcessor

class VoiceAgent:
    """
    Handles voice recognition and speech synthesis for FlexiBuddy.
    Uses Whisper for voice recognition and Coqui TTS for synthesis.
    Includes NLP processing for better understanding of children's speech.
    """
    def __init__(self):
        # Initialize NLP processor
        self.nlp_processor = NLPProcessor()
        
        # Initialize speech recognition model
        self.whisper_model = None
        try:
            # Load the smallest model for faster processing
            self.whisper_model = whisper.load_model("tiny")
            self.speech_recognition_loaded = True
            print("Whisper speech recognition model loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.speech_recognition_loaded = False
        
        # Initialize the speech synthesis model
        self.tts = None
        try:
            # Use a friendly, clear voice model
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            self.voice_model_loaded = True
            print("TTS voice synthesis model loaded successfully")
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            self.voice_model_loaded = False
        
        # Audio recording configuration
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        
        # Configurations from app settings
        self.speech_rate = APP_CONFIG.get("speech_rate", 0.8)  # Lower = slower
        self.voice_pitch = APP_CONFIG.get("voice_pitch", 1.0)  # Voice pitch
        
        # Temporary output path
        self.temp_dir = tempfile.gettempdir()
    
    def listen(self, duration=5):
        """
        Listens to user audio input and converts it to text.
        Works on both Windows and Linux platforms.
        
        Args:
            duration (int): Recording duration in seconds
            
        Returns:
            str: Recognized text or None if recognition failed
        """
        if not self.speech_recognition_loaded:
            print("Voice recognition not available.")
            return None
        
        try:
            # Create temporary file for recording
            temp_file = os.path.join(self.temp_dir, f"audio_input_{time.time()}.wav")
            
            # Record audio using PyAudio (cross-platform)
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("Recording...")
            frames = []
            for i in range(0, int(self.rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)
            
            print("Recording finished")
            stream.stop_stream()
            stream.close()
            
            # Save recording to WAV file
            wf = wave.open(temp_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Load recorded audio for Whisper
            audio = whisper.load_audio(temp_file)
            audio = whisper.pad_or_trim(audio)
            
            # Generate log-Mel features of the audio
            mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)
            
            # Detect language using Whisper model
            _, probs = self.whisper_model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            # Decode audio to text
            options = whisper.DecodingOptions(language=detected_language, fp16=False)
            result = whisper.decode(self.whisper_model, mel, options)
            
            # Process text through NLP processor for better understanding
            if result.text:
                nlp_result = self.nlp_processor.process_input(result.text)
                print(f"Detected intent: {nlp_result['intent']} (confidence: {nlp_result['confidence']:.2f})")
            
            # Clean temporary files
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return result.text
        
        except Exception as e:
            print(f"Error during listening: {e}")
            return None
    
    def speak(self, text, slow_mode=False):
        """
        Converts text to speech using Coqui TTS.
        If slow_mode is True, further slows down the speech for better comprehension.
        
        Args:
            text (str): Text to convert to speech
            slow_mode (bool): If True, speaks more slowly
            
        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        if not self.voice_model_loaded:
            print(f"Voice synthesis not available. Message: {text}")
            return False
        
        try:
            # Simplify text for better understanding
            simplified_text = self.nlp_processor.simplify_text(text)
            
            # Adjust speech rate based on slow_mode
            rate = self.speech_rate * 0.7 if slow_mode else self.speech_rate
            
            # Create temporary output file
            temp_output = os.path.join(self.temp_dir, f"speech_output_{time.time()}.wav")
            
            # Generate audio file with speech synthesis
            self.tts.tts_to_file(
                text=simplified_text,
                file_path=temp_output,
                speaker=self.tts.speakers[0] if hasattr(self.tts, 'speakers') and self.tts.speakers else None,
                speed=rate
            )
            
            # Play audio in a separate thread to not block the interface
            threading.Thread(target=self._play_audio, args=(temp_output,)).start()
            
            return True
        
        except Exception as e:
            print(f"Error during voice synthesis: {e}")
            return False
    
    def _play_audio(self, audio_file):
        """
        Plays an audio file using the appropriate method based on the operating system.
        
        Args:
            audio_file (str): Path to the audio file to play
        """
        try:
            if os.name == 'posix':  # Linux
                subprocess.run(["aplay", audio_file])
            elif os.name == 'nt':  # Windows
                # Use Windows Media Player to play the audio
                os.system(f'start wmplayer "{audio_file}"')
            
            # Wait a bit before cleaning up
            time.sleep(1)
            
            # Clean up the temporary file
            if os.path.exists(audio_file):
                os.remove(audio_file)
        
        except Exception as e:
            print(f"Error during audio playback: {e}")
    
    def detect_intent(self, text):
        """
        Detects the intent of the user's speech using the NLP processor
        
        Args:
            text (str): User's speech text
            
        Returns:
            tuple: (intent, confidence)
        """
        if not text:
            return ('unknown', 0.0)
        
        # Use NLP processor to detect intent
        result = self.nlp_processor.process_input(text)
        return (result['intent'], result['confidence'])
    
    def generate_response(self, intent, confidence=0.0):
        """
        Generates a response based on the detected intent
        
        Args:
            intent (str): Detected intent
            confidence (float): Confidence score
            
        Returns:
            str: Response text
        """
        return self.nlp_processor.generate_response(intent, confidence)
    
    def process_command(self, text):
        """
        Processes a voice command and determines the appropriate action
        
        Args:
            text (str): Voice command text
            
        Returns:
            dict: Command processing results
        """
        intent, confidence = self.detect_intent(text)
        
        # Map intents to actions
        action = None
        if intent == 'bored' or intent == 'change_activity':
            action = 'change_activity'
        elif intent == 'stop':
            action = 'stop'
        elif intent == 'help':
            action = 'help'
        elif intent == 'repeat':
            action = 'repeat'
        elif intent == 'slower':
            action = 'slow_mode'
        
        # Generate response
        response = self.generate_response(intent, confidence)
        
        return {
            'text': text,
            'intent': intent,
            'confidence': confidence,
            'action': action,
            'response': response
        }
