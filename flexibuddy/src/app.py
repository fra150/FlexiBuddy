import streamlit as st
import time
import random
from PIL import Image
import os
import sys

# Add the parent directory to the Python path to allow importing custom modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.voice_agent import VoiceAgent 
from src.activity_switcher import ActivitySwitcher 
from src.data_logger import DataLogger 
from src.utils.config import APP_CONFIG 
from src.utils.animations import load_animation 
from src.ai_models.nlp_processor import NLPProcessor
from src.ai_models.recommendation_engine import RecommendationEngine
from src.ai_models.emotion_detector import EmotionDetector

# Configure the Streamlit page settings
st.set_page_config(
    page_title="FlexiBuddy - Your Educational Companion",
    page_icon="🐻",  # Favicon
    layout="wide",    # Use wide layout
    initial_sidebar_state="collapsed" # Keep sidebar closed initially
)

# Function to load custom CSS styles from a file
def load_css():
    css_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'styles.css')
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning("CSS file not found. Using default styling.")

# Function to initialize session state variables if they don't exist
def initialize_session_state():
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    if 'activity_start_time' not in st.session_state:
        st.session_state.activity_start_time = time.time()
    if 'current_activity' not in st.session_state:
        st.session_state.current_activity = "welcome"
    if 'points' not in st.session_state:
        st.session_state.points = 0
    if 'frustration_moments' not in st.session_state:
        st.session_state.frustration_moments = 0
    if 'completed_activities' not in st.session_state:
        st.session_state.completed_activities = []
    if 'user_name' not in st.session_state:
        st.session_state.user_name = "Friend"
    if 'avatar_state' not in st.session_state:
        st.session_state.avatar_state = "happy"
    if 'emotion' not in st.session_state:
        st.session_state.emotion = "neutral"
    if 'ai_insights' not in st.session_state:
        st.session_state.ai_insights = ""
    if 'slow_mode' not in st.session_state:
        st.session_state.slow_mode = False

# Function to record details when an activity is completed
def complete_activity(activity_name, duration, success=True):
    st.session_state.completed_activities.append({
        "activity": activity_name,
        "duration": round(duration, 2), 
        "success": success,
        "timestamp": time.time()
    })
    st.session_state.activity_start_time = time.time()
    data_logger.log_activity_completion(activity_name, duration, success)

# Function to change the current activity
def change_activity(reason="timeout"): # Default reason is automatic timeout
    current_time = time.time()
    duration = current_time - st.session_state.activity_start_time

    # Assuming success is True by default when changing activity (can be refined)
    complete_activity(st.session_state.current_activity, duration, success=True)
    
    # Try to get AI recommendation first
    ai_recommendation = ai_integration.get_activity_recommendation(
        current_activity=st.session_state.current_activity,
        reason=reason,
        frustration_level=st.session_state.frustration_moments
    )
    
    # Use AI recommendation if available, otherwise use activity switcher
    if ai_recommendation:
        new_activity = ai_recommendation
        print(f"Using AI recommendation: {new_activity}")
    else:
        new_activity = activity_switcher.get_next_activity(
            current_activity=st.session_state.current_activity,
            reason=reason, 
            frustration_level=st.session_state.frustration_moments 
        )

    st.session_state.current_activity = new_activity
    st.session_state.activity_start_time = current_time
    voice_agent.speak(f"Let's change the game! Now we play {new_activity.replace('_', ' ')}!") 
    
    # Generate a new AI insight when changing activities
    st.session_state.ai_insights = ai_integration.generate_insight(
        user_name=st.session_state.user_name,
        current_activity=new_activity
    )

    st.rerun()

# Function to handle the "I'm bored" button click or voice command
def handle_boredom():
    st.session_state.frustration_moments += 1
    
    # Log the frustration moment with current activity
    data_logger.log_frustration_moment(activity=st.session_state.current_activity)
    
    # Get personalized response from AI if available
    if 'ai_integration' in st.session_state:
        # Generate a response based on current emotion and activity
        response = ai_integration.process_input(
            "I'm bored", 
            current_activity=st.session_state.current_activity,
            user_name=st.session_state.user_name
        )
        
        # Use the AI-generated response if available
        if response and 'response' in response:
            voice_agent.speak(response['response'])
    
    # Change to a new activity
    change_activity(reason="boredom")

# Function to listen for voice commands using the voice agent
def listen_for_commands():
    command = voice_agent.listen()
    if command:
        command_lower = command.lower()
        
        # Process command with AI integration if available
        if 'ai_integration' in st.session_state:
            # Get AI-enhanced understanding of the command
            result = ai_integration.process_input(
                command,
                current_activity=st.session_state.current_activity,
                user_name=st.session_state.user_name
            )
            
            # Check for intents based on AI processing
            intent = result.get('intent', 'unknown')
            confidence = result.get('confidence', 0.0)
            
            if intent == 'bored' and confidence > 0.3:
                handle_boredom()
            elif intent == 'change_activity' and confidence > 0.3:
                change_activity(reason="voice_command")
            elif intent in ['confused', 'help'] and confidence > 0.3:
                # Provide help based on current activity
                voice_agent.speak(f"Let me explain how to play {st.session_state.current_activity.replace('_', ' ')}. Take your time and have fun!")
            
            # Update emotion if detected
            if 'emotion' in result and result['emotion'] != 'neutral':
                st.session_state.emotion = result['emotion']
            
            # If AI provided a response, speak it
            if 'response' in result and result['response']:
                voice_agent.speak(result['response'])
        
        # Fallback to basic command detection
        else:
            if "i'm bored" in command_lower or "bored" in command_lower:
                handle_boredom()
            elif "change game" in command_lower or "change activity" in command_lower:
                change_activity(reason="voice_command")
        
        return command
    return None

# Main function defining the Streamlit user interface
def main():
    load_css()
    initialize_session_state()
    
    # Initialize AI components
    global voice_agent, activity_switcher, data_logger, nlp_processor, recommendation_engine, emotion_detector, ai_integration
    
    # Create data logger first as it's needed by other components
    if 'data_logger' not in st.session_state:
        st.session_state.data_logger = DataLogger()
        data_logger = st.session_state.data_logger
    else:
        data_logger = st.session_state.data_logger
    
    # Create NLP processor
    if 'nlp_processor' not in st.session_state:
        st.session_state.nlp_processor = NLPProcessor()
        nlp_processor = st.session_state.nlp_processor
    else:
        nlp_processor = st.session_state.nlp_processor
    
    # Create recommendation engine
    if 'recommendation_engine' not in st.session_state:
        st.session_state.recommendation_engine = RecommendationEngine(data_logger)
        recommendation_engine = st.session_state.recommendation_engine
    else:
        recommendation_engine = st.session_state.recommendation_engine
    
    # Create emotion detector
    if 'emotion_detector' not in st.session_state:
        st.session_state.emotion_detector = EmotionDetector()
        emotion_detector = st.session_state.emotion_detector
    else:
        emotion_detector = st.session_state.emotion_detector
        
    # Create AI integration to coordinate all AI components
    if 'ai_integration' not in st.session_state:
        from src.ai_models.ai_integration import AIIntegration
        st.session_state.ai_integration = AIIntegration(
            nlp_processor=nlp_processor,
            emotion_detector=emotion_detector,
            recommendation_engine=recommendation_engine,
            data_logger=data_logger
        )
        ai_integration = st.session_state.ai_integration
    else:
        ai_integration = st.session_state.ai_integration
    
    # Create activity switcher with data logger and recommendation engine
    if 'activity_switcher' not in st.session_state:
        st.session_state.activity_switcher = ActivitySwitcher(data_logger)
        activity_switcher = st.session_state.activity_switcher
    else:
        activity_switcher = st.session_state.activity_switcher
    
    # Create voice agent
    if 'voice_agent' not in st.session_state:
        st.session_state.voice_agent = VoiceAgent()
        voice_agent = st.session_state.voice_agent
    else:
        voice_agent = st.session_state.voice_agent
    
    col1, col2 = st.columns([1, 3]) 

    # Left Column -Avatar
    with col1:
        # Here e based on its current state (e.g., 'happy', 'thinking')
        avatar_image_path = load_animation(st.session_state.avatar_state)
        if avatar_image_path: 
             st.image(avatar_image_path, width=200) 
        else:
             st.write("Avatar") 

    with col2:
        # Here I display the main title with the user's name
        st.title(f"Hello {st.session_state.user_name}! 👋")
        st.subheader("I'm FlexiBuddy, your friend for learning while having fun!")

        # Here I display the user's current points using st.metric
        st.metric("Star Points ⭐", st.session_state.points)
        activity_duration = time.time() - st.session_state.activity_start_time
        max_duration = APP_CONFIG.get("max_activity_duration", 300) # Default 300s (5 min)
        progress = min(activity_duration / max_duration, 1.0)
        st.progress(progress)
        
        # Display AI insights if available
        if st.session_state.ai_insights:
            st.info(st.session_state.ai_insights)
        
        # Update emotion detection periodically
        if time.time() % 10 < 0.1:  # Check roughly every 10 seconds
            emotion, confidence = emotion_detector.get_current_emotion()
            if confidence > 0.4:  # Only update if confidence is reasonable
                st.session_state.emotion = emotion
                # Update avatar state based on emotion
                if emotion == "happy":
                    st.session_state.avatar_state = "happy"
                elif emotion in ["sad", "angry"]:
                    st.session_state.avatar_state = "sad"
                elif emotion == "surprised":
                    st.session_state.avatar_state = "surprised"
                elif emotion == "confused":
                    st.session_state.avatar_state = "thinking"

        # Here I add the "I'm bored" button
        if st.button("😕 I'm bored!", key="boredom_button", use_container_width=True):
            handle_boredom() # Call the handler function when clicked

    # Add a visual separator
    st.markdown("---")

    # --- Main Activity Area ---
    # Display the title of the current activity
    activity_title = st.session_state.current_activity.replace('_', ' ').title()
    st.header(f"We are playing: {activity_title}")

    # Here I check if the current activity duration has exceeded the maximum limit
    if activity_duration > max_duration:
        change_activity(reason="timeout") # Trigger automatic change if time is up

    # Here I display the content based on the current activity name
    # Using if/elif/else to route to the correct display function
    if st.session_state.current_activity == "welcome":
        show_welcome_activity()
    elif st.session_state.current_activity == "memory_game":
        show_memory_game()
    elif st.session_state.current_activity == "quiz_game":
        show_quiz_game()
    elif st.session_state.current_activity == "drawing_activity":
        show_drawing_activity()
    elif st.session_state.current_activity == "mindfulness_break":
        show_mindfulness_activity()
    else:
        # Fallback if the activity name is somehow unknown
        st.warning("Unknown activity. Let's choose another one!")
        change_activity(reason="error") 

    # Add another visual separator
    st.markdown("---")
    voice_col1, voice_col2 = st.columns([3, 1])

    with voice_col1:
        st.text("You can tell me 'I'm bored' or 'Change game' anytime!")

    with voice_col2:
        if st.button("🎤 Talk to me!", key="voice_button"):
            st.info("Listening...") 
            command = listen_for_commands() 
            if command:
                st.write(f"I heard: {command}")
            else:
                st.write("Didn't catch that. Try again?")

# Function to display the Welcome screen/activity
def show_welcome_activity():
    st.write("Welcome to FlexiBuddy! I'm here to help you learn and have fun together.")
    st.write("You can tell me 'I'm bored' anytime you want to change the game.")
    if st.session_state.user_name == "Friend":
        user_name_input = st.text_input("What's your name?")
        if user_name_input:
            st.session_state.user_name = user_name_input
            voice_agent.speak(f"Hello {user_name_input}! I'm happy to meet you!")
            st.rerun()

    # Add a button to manually start the first 'real' activity
    if st.button("Let's start playing!", key="start_button"):
        change_activity(reason="user_start") # Change activity because user clicked start

# Function to display the Memory Game activity
def show_memory_game():
    st.write("Memory Game: Remember the sequence of images!")

    # Define the pool of items for the memory game (using emojis)
    memory_items = ["🐶", "🐱", "🐭", "🦊", "🐻", "🐼", "🐨", "🦁"]

    # Initialize game state within session_state if it doesn't exist for this round
    if 'memory_sequence' not in st.session_state:
        # Use AI to adapt difficulty if available
        if 'ai_integration' in st.session_state:
            # Get success rate from previous memory games
            success_history = [item for item in st.session_state.completed_activities 
                              if item['activity'] == 'memory_game']
            success_rate = sum(1 for item in success_history if item['success']) / max(1, len(success_history))
            
            # Get adaptive difficulty parameters
            difficulty = ai_integration.adapt_difficulty('memory_game', success_rate)
            items_count = difficulty.get('items_count', 3)  # Default to 3 if not specified
            
            st.session_state.memory_sequence = random.sample(memory_items, items_count)
        else:
            # Default behavior without AI
            st.session_state.memory_sequence = random.sample(memory_items, 3)
            
        st.session_state.memory_display_phase = True
        st.session_state.memory_start_time = time.time()
        st.session_state.user_memory_selection = []

    # here Display Phase
    if st.session_state.memory_display_phase:
        # Show the sequence to memorize (large emojis)
        st.markdown(f"<h1 style='text-align: center; letter-spacing: 15px;'>{''.join(st.session_state.memory_sequence)}</h1>", unsafe_allow_html=True)
        st.caption("Remember these!")

        # Here I check if the display time (e.g., 3 seconds) has passed
        if time.time() - st.session_state.memory_start_time > 3:
            # Switch to the input phase
            st.session_state.memory_display_phase = False
            # Rerun to update the UI for the input phase
            st.rerun()

    # here Input Phase 
    else:
        st.write("Which animals did you see? Select them in the correct order:")
        st.write(f"Your sequence: `{' '.join(st.session_state.user_memory_selection)}`")
        cols = st.columns(len(memory_items)) # Create one column per item
        for i, item in enumerate(memory_items):
            # When a button is clicked
            if cols[i].button(item, key=f"memory_{item}_{st.session_state.activity_start_time}"): # Unique key per round
                # Add the selected item to the user's sequence
                st.session_state.user_memory_selection.append(item)

                # Here I check if the user has selected enough items
                if len(st.session_state.user_memory_selection) == len(st.session_state.memory_sequence):
                    # Check if the user's sequence matches the correct sequence
                    if st.session_state.user_memory_selection == st.session_state.memory_sequence:
                        st.success("Great job! You remembered correctly!")
                        voice_agent.speak("Fantastic! You have an excellent memory!")
                        st.session_state.points += 10 # Award points
                    else:
                        correct_sequence_str = ' '.join(st.session_state.memory_sequence)
                        st.error(f"Oops, not quite right. The sequence was: {correct_sequence_str}. Let's try again!")
                        voice_agent.speak("Don't worry, we can try again!")
                        st.session_state.frustration_moments += 0.5 # Increment frustration slightly
                    del st.session_state.memory_sequence
                    del st.session_state.memory_display_phase
                    del st.session_state.memory_start_time
                    del st.session_state.user_memory_selection
                    time.sleep(3)
                    st.rerun()
                else:
                    st.rerun()


# Function to display the Quiz Game activity
def show_quiz_game():
    st.write("Educational Quiz: Answer the questions!")

    # Define a list of simple quiz questions suitable for children
    quiz_questions = [
        # Level 1 (Easy)
        {"question": "Which animal says 'meow'?", "options": ["Dog", "Cat", "Cow", "Sheep"], "answer": "Cat", "level": 1},
        {"question": "How many fingers do you have on one hand?", "options": ["3", "5", "8", "10"], "answer": "5", "level": 1},
        {"question": "What color is the sky on a clear day?", "options": ["Green", "Red", "Blue", "Yellow"], "answer": "Blue", "level": 1},
        {"question": "Which fruit is typically yellow and curved?", "options": ["Apple", "Banana", "Strawberry", "Grape"], "answer": "Banana", "level": 1},
        
        # Level 2 (Medium)
        {"question": "Which season comes after summer?", "options": ["Winter", "Spring", "Fall", "None of these"], "answer": "Fall", "level": 2},
        {"question": "How many sides does a triangle have?", "options": ["2", "3", "4", "5"], "answer": "3", "level": 2},
        {"question": "Which planet do we live on?", "options": ["Mars", "Earth", "Jupiter", "Moon"], "answer": "Earth", "level": 2},
        {"question": "What do plants need to grow?", "options": ["Candy", "Water", "Toys", "Books"], "answer": "Water", "level": 2},
        
        # Level 3 (Hard)
        {"question": "Which of these animals is a mammal?", "options": ["Fish", "Snake", "Dolphin", "Lizard"], "answer": "Dolphin", "level": 3},
        {"question": "What is the largest ocean on Earth?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "answer": "Pacific", "level": 3},
        {"question": "How many continents are there in the world?", "options": ["5", "6", "7", "8"], "answer": "7", "level": 3},
        {"question": "Which of these is NOT a state of matter?", "options": ["Solid", "Liquid", "Gas", "Rock"], "answer": "Rock", "level": 3}
    ]

    # Initialize the state for the current question if it doesn't exist
    if 'current_quiz_question' not in st.session_state or st.session_state.current_quiz_question is None:
        # Use AI to adapt difficulty if available
        if 'ai_integration' in st.session_state:
            # Get success rate from previous quiz games
            success_history = [item for item in st.session_state.completed_activities 
                              if item['activity'] == 'quiz_game']
            success_rate = sum(1 for item in success_history if item['success']) / max(1, len(success_history))
            
            # Get adaptive difficulty parameters
            difficulty = ai_integration.adapt_difficulty('quiz_game', success_rate)
            question_level = difficulty.get('question_level', 1)  # Default to level 1 if not specified
            
            # Filter questions by level
            level_questions = [q for q in quiz_questions if q.get('level', 1) <= question_level]
            if level_questions:
                st.session_state.current_quiz_question = random.choice(level_questions)
            else:
                st.session_state.current_quiz_question = random.choice(quiz_questions)
        else:
            # Default behavior without AI
            st.session_state.current_quiz_question = random.choice(quiz_questions)
            
        # Speak the question using the voice agent
        voice_agent.speak(st.session_state.current_quiz_question["question"])

    # Get the current question details
    question_data = st.session_state.current_quiz_question

    # Display the question
    st.subheader(question_data["question"])

    # Create buttons for each answer option
    for option in question_data["options"]:
        # When an option button is clicked
        if st.button(option, key=f"quiz_{option.replace(' ', '_')}_{st.session_state.activity_start_time}"): # Unique key per round
            # Check if the selected option is the correct answer
            if option == question_data["answer"]:
                st.success("Correct! You're amazing!")
                voice_agent.speak("Correct answer! You are very smart!")
                st.session_state.points += 5 # Award points
            else:
                st.error(f"Not quite. The correct answer is {question_data['answer']}. Keep trying!")
                voice_agent.speak(f"Don't worry! The right answer is {question_data['answer']}")
                st.session_state.frustration_moments += 0.5 # Increment frustration slightly

            # Reset the current question to prepare for the next one
            st.session_state.current_quiz_question = None
            # Add a short delay before showing the next question
            time.sleep(2)
            # Rerun Streamlit to pick and display the next question
            st.rerun()

# Function to display the Drawing Activity
def show_drawing_activity():
    st.write("Let's draw together! Use your imagination!")

    try:
        # Import the drawable canvas component only when needed
        from streamlit_drawable_canvas import st_canvas

        # Define a list of drawing prompts
        drawing_prompts = [
            "Draw a happy tree",
            "Draw your family",
            "Draw a funny animal",
            "Draw your dream house",
            "Draw something that makes you happy"
        ]

        # Initialize the drawing prompt for this session if it doesn't exist
        if 'drawing_prompt' not in st.session_state or st.session_state.drawing_prompt is None:
            # Choose a random prompt
            st.session_state.drawing_prompt = random.choice(drawing_prompts)
            # Speak the prompt using the voice agent
            voice_agent.speak(f"Let's draw! How about you {st.session_state.drawing_prompt.lower()}?")

        # Display the current drawing prompt
        st.subheader(st.session_state.drawing_prompt)

        # Create the drawing canvas component
        canvas_result = st_canvas(
            stroke_width=st.sidebar.slider("Stroke width", 1, 25, 3), # Allow changing stroke width via sidebar
            stroke_color=st.sidebar.color_picker("Stroke color", "#000000"), # Allow changing color
            background_color="rgba(255, 255, 255, 0.8)", # White background
            update_streamlit=True, # Send drawing data back to Streamlit in real time
            height=400,
            width=700,
            drawing_mode=st.sidebar.selectbox("Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")), # Add drawing tools
            key="canvas"
        )

        # Add a button for when the user finishes drawing
        if st.button("I finished my drawing!", key="drawing_done"):
            # Check if there is actually image data from the canvas
            if canvas_result.image_data is not None:
                st.success("What a beautiful drawing! You are very creative!")
                voice_agent.speak("I really like your drawing! You are a true artist!")
                st.session_state.points += 8 # Award points
                st.session_state.drawing_prompt = None
                time.sleep(2)
                st.rerun()
            else:
                st.warning("Looks like the canvas is empty. Draw something!")

    except ImportError:
        st.error("Sorry, I can't load the drawing activity right now. Let's change the game!")
        change_activity(reason="module_error")

def show_mindfulness_activity():
    st.write("Mindfulness Break: Let's relax together!")

    # Define a list of simple mindfulness exercises for children
    exercises = [
        {
            "title": "Butterfly Breath",
            "instruction": "Breathe in, raising your arms like butterfly wings, and breathe out, lowering them slowly. Feel calm.",
            "duration": 15 # Duration in seconds
        },
        {
            "title": "Listening Ears",
            "instruction": "Close your eyes gently. Listen carefully. How many different sounds can you hear around you? Just listen.",
            "duration": 20
        },
        {
            "title": "Body Scan",
            "instruction": "Sit comfortably. Close your eyes. Feel your toes relax, then your feet, your legs... all the way up to your head. Feel calm and still.",
            "duration": 25
        }
    ]

    # Initialize the state for the current mindfulness exercise if it doesn't exist
    if 'mindfulness_exercise' not in st.session_state or st.session_state.mindfulness_exercise is None:
        # Select a random exercise
        exercise = random.choice(exercises)
        
        # Use AI to adapt duration if available
        if 'ai_integration' in st.session_state:
            # Get success rate from previous mindfulness activities
            success_history = [item for item in st.session_state.completed_activities 
                              if item['activity'] == 'mindfulness_break']
            success_rate = sum(1 for item in success_history if item['success']) / max(1, len(success_history))
            
            # Get adaptive difficulty parameters
            difficulty = ai_integration.adapt_difficulty('mindfulness_break', success_rate)
            duration = difficulty.get('duration', exercise['duration'])  # Use AI duration or default
            
            # Create a copy of the exercise with the adapted duration
            exercise = exercise.copy()
            exercise['duration'] = duration
        
        st.session_state.mindfulness_exercise = exercise
        st.session_state.mindfulness_start_time = time.time()
        voice_agent.speak(f"Let's try {st.session_state.mindfulness_exercise['title']}. {st.session_state.mindfulness_exercise['instruction']}")

    exercise = st.session_state.mindfulness_exercise
    elapsed_time = time.time() - st.session_state.mindfulness_start_time
    remaining_time = max(0, exercise["duration"] - elapsed_time)
    st.subheader(exercise["title"])
    st.write(exercise["instruction"])
    # Display a visual timer (progress bar)
    progress = (elapsed_time / exercise["duration"]) if exercise["duration"] > 0 else 1.0
    st.progress(min(progress, 1.0)) # Ensure progress doesn't exceed 1.0
    st.write(f"Time remaining: {int(remaining_time)} seconds")

    # Check if the exercise duration has completed
    if remaining_time <= 0:
        st.success("Great job! Do you feel more relaxed now?")
        voice_agent.speak("Wonderful! Your mind is calm and relaxed. You did very well!")
        st.session_state.points += 6 
        st.session_state.mindfulness_exercise = None
        time.sleep(3)
        st.rerun()

# Initialization of custom classes
voice_agent = VoiceAgent() 
activity_switcher = ActivitySwitcher() 
data_logger = DataLogger() # Logs data points like activity completion, frustration
#  Start the Streamlit application execution 
if __name__ == "__main__":
    main()