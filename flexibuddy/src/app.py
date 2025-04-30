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
    new_activity = activity_switcher.get_next_activity(
        current_activity=st.session_state.current_activity,
        reason=reason, 
        frustration_level=st.session_state.frustration_moments 
    )

    st.session_state.current_activity = new_activity
    st.session_state.activity_start_time = current_time
    voice_agent.speak(f"Let's change the game! Now we play {new_activity.replace('_', ' ')}!") 

    st.rerun()

# Function to handle the "I'm bored" button click or voice command
def handle_boredom():
    st.session_state.frustration_moments += 1
    data_logger.log_frustration_moment()
    change_activity(reason="boredom")

# Function to listen for voice commands using the voice agent
def listen_for_commands():
    command = voice_agent.listen()
    if command:
        command_lower = command.lower()
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
        {"question": "Which animal says 'meow'?", "options": ["Dog", "Cat", "Cow", "Sheep"], "answer": "Cat"},
        {"question": "How many fingers do you have on one hand?", "options": ["3", "5", "8", "10"], "answer": "5"},
        {"question": "What color is the sky on a clear day?", "options": ["Green", "Red", "Blue", "Yellow"], "answer": "Blue"},
        {"question": "Which fruit is typically yellow and curved?", "options": ["Apple", "Banana", "Strawberry", "Grape"], "answer": "Banana"}
    ]

    # Initialize the state for the current question if it doesn't exist
    if 'current_quiz_question' not in st.session_state or st.session_state.current_quiz_question is None:
        # Randomly choose a question from the list
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
        st.session_state.mindfulness_exercise = random.choice(exercises)
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