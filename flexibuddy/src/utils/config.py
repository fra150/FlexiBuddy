"""
Here Global configurations for FlexiBuddy
"""
# Application configuration
APP_CONFIG = {
    # Activity duration settings
    "max_activity_duration": 180,  # 3 minutes in seconds
    "min_activity_duration": 60,   # 1 minute in seconds
    
    # Voice configuration
    "speech_rate": 0.8,            # Lower = slower speech
    "voice_pitch": 1.0,            # Voice pitch level
    
    # User interface
    "use_large_text": True,        # Larger text for readability
    "use_high_contrast": False,    # High contrast for visibility
    "use_animations": True,        # Animations for visual feedback
    
    # Data collection and reporting
    "auto_share_reports": False,   # Automatic report sharing
    "share_with_parents": True,    # Share with parents
    "share_with_teachers": False,  # Share with teachers
    "share_with_healthcare": False, # Share with healthcare providers
    
    # Sharing email addresses (example)
    "parent_email": "",
    "teacher_email": "",
    "healthcare_email": "",
    
    # Offline mode options
    "offline_mode": False,         # Operation without connection
    "save_audio_locally": False,   # Save audio files locally
}
# Games and activities configuration
GAMES_CONFIG = {
    "memory": {
        "difficulty_levels": 3,    # Available difficulty levels
        "initial_level": 1,        # Starting level
        "items_per_level": [3, 5, 7],  # Number of items per level
        "display_time": 3          # Display time in seconds
    },
    "quiz": {
        "difficulty_levels": 3,    # Available difficulty levels
        "initial_level": 1,        # Starting level
        "questions_per_session": 5 # Questions per session
    },
    "drawing": {
        "available_colors": ["black", "red", "blue", "green", "yellow"],
        "brush_sizes": [3, 5, 8],  # Brush sizes
        "default_brush_size": 5    # Default size
    },
    "mindfulness": {
        "exercise_duration": 20,   # Exercise duration in seconds
        "background_music": True   # Plays background music
    }
}