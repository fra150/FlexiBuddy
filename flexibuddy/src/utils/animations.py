import os
import time
from PIL import Image
import streamlit as st
from src.utils.config import APP_CONFIG

def load_animation(state="happy"):
    """
    I'm loading the avatar image based on its emotional state
    Args:
        state (str): Avatar's emotional state ('happy', 'thinking', 'surprised', 'sad')   
    Returns:
        Image: Avatar image
    """
    # Here I'm getting the images directory path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    images_dir = os.path.join(base_dir, 'assets', 'images')
    
    # I'm mapping states to their corresponding image files
    state_images = {
        "happy": "avatar_happy.png",
        "thinking": "avatar_thinking.png",
        "surprised": "avatar_surprised.png",
        "sad": "avatar_sad.png"
    }
    
    # I'm setting a default image if the state isn't recognized
    image_file = state_images.get(state, "avatar_happy.png")
    image_path = os.path.join(images_dir, image_file)
    
    # I'm creating a fallback image if the file doesn't exist
    if not os.path.exists(image_path):
        return _create_fallback_image(state)
    
    # I'm loading and returning the image
    return Image.open(image_path)

def animate_transition(from_state, to_state, duration=1.0):
    """
    I'm animating the transition between two avatar states
    
    Args:
        from_state (str): Initial state
        to_state (str): Final state
        duration (float): Animation duration in seconds
    """
    if not APP_CONFIG.get("use_animations", True):
        return
    
    # I'm loading images for both states
    from_image = load_animation(from_state)
    to_image = load_animation(to_state)
    
    # I'm creating a container for the animation
    container = st.empty()
    
    # I'm setting up animation frames
    steps = 10
    step_duration = duration / steps
    
    # I'm executing the animation
    for i in range(steps + 1):
        # I'm calculating the blend ratio
        alpha = i / steps
        
        # I'm blending the images (simple crossfade)
        if hasattr(Image, 'blend'):
            # I'm using PIL's blend if available
            blended = Image.blend(from_image, to_image, alpha)
        else:
            # I'm just showing the target image if blending isn't supported
            blended = to_image
        # I'm updating the container with the blended image
        container.image(blended, width=200)
        # I'm pausing for the frame duration
        time.sleep(step_duration)

def _create_fallback_image(state="happy"):
    """
    I'm creating a fallback image when avatar images aren't available
    Args:
        state (str): Emotional state to represent  
    Returns:
        Image: Generated fallback image
    """
    # I'm mapping states to emoji
    emoji_map = {
        "happy": "😊",
        "thinking": "🤔",
        "surprised": "😲",
        "sad": "😞"
    }
    
    # I'm setting a default emoji if state isn't recognized
    emoji = emoji_map.get(state, "😊")
    
    # I'm creating an empty image with emoji
    image = Image.new('RGB', (200, 200), color=(255, 255, 255))
    
    # I could use PIL to draw the emoji, but it's complex
    # For simplicity, I'm just returning the empty image
    return image