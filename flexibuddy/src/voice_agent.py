import os
import subprocess
import threading
import time
import tempfile
import wave
import numpy as np
import whisper
from TTS.api import TTS
from src.utils.config import APP_CONFIG

class VoiceAgent:
    """
    Handles voice recognition and speech synthesis for FlexiBuddy.
    Uses Whisper for voice recognition and Coqui TTS for synthesis.
    """
    def __init__(self):
        self.whisper_model = None
        try:
            self.whisper_model = whisper.load_model("tiny")  
            self.speech_recognition_loaded = True
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.speech_recognition_loaded = False
        
        # I initialize the speech synthesis model
        self.tts = None
        try:
            self.tts = TTS(model_name="tts_models/it/mai/tacotron2-DDC")
            self.voice_model_loaded = True
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            self.voice_model_loaded = False
        
        # Configurations
        self.speech_rate = APP_CONFIG.get("speech_rate", 0.8)  # Lower = slower
        self.voice_pitch = APP_CONFIG.get("voice_pitch", 1.0)  # Voice pitch
        
        # Temporary output path
        self.temp_dir = tempfile.gettempdir()
    
    def listen(self, duration=5, sample_rate=16000):
        """
        Listens to user audio input and converts it to text.
        """
        if not self.speech_recognition_loaded:
            print("Voice recognition not available.")
            return None
        try:
            # Temporary file name for recording
            temp_file = os.path.join(self.temp_dir, f"audio_input_{time.time()}.wav")
            if os.name == 'posix':  # Linux
                subprocess.run(["arecord", "-r", str(sample_rate), "-f", "S16_LE", "-d", str(duration), "-c", "1", temp_file])
            elif os.name == 'nt':  # Windows
                print("Recording on Windows not implemented in this example 18:(96)")
                return None
            # Load recorded audio
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
        If slow_mode is True, further slows down the speech.
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
            rate = self.speech_rate * 0.7 if slow_mode else self.speech_rate
            temp_output = os.path.join(self.temp_dir, f"speech_output_{time.time()}.wav")
            
            # Generate audio file with speech synthesis
            self.tts.tts_to_file(
                text=text,
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
        Plays an audio file using the appropriate library based on the operating system.
        Args:
            audio_file (str): Path to the audio file to play
        """
        try:
            if os.name == 'posix':  # Linux
                subprocess.run(["aplay", audio_file])
            elif os.name == 'nt':  # Windows
                subprocess.run(["start", audio_file], shell=True)
            
            time.sleep(1)
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            print(f"Error during audio playback: {e}")
