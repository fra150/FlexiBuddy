# FlexiBuddy – AI Educational Assistant for Neurodiverse Children
FlexiBuddy is an AI-powered educational companion designed for hyperactive children and those with learning disabilities. It adapts, switches activities quickly, speaks in simplified language, and sends useful feedback to parents, teachers, and healthcare providers.

## 🎯 Goal
Support hyperactive children or those with learning disabilities through a flexible, free AI agent that:
- Communicates slowly and clearly, adapting words and tone  
- Switches activities rapidly to maintain the child’s attention  
- Provides educational entertainment (games, animations, voice quizzes)  
- Extracts interaction data and sends it securely in simple formats to parents, schools, and healthcare professionals  
- Works offline or locally to protect privacy  
- Uses free or open-source technologies (local models or free APIs)  

## 🧠 Key Features

### 🗣️ Adaptive Communication
- Speaks slowly and clearly, with an option to slow down further on request  
- Uses simple words, short sentences, images, and emojis to enhance understanding  
- Displays visual feedback (an avatar) that repeats or illustrates what is said  

### 🔄 Rapid Activity Switching
- After 3–5 minutes, automatically suggests a new activity (quiz, game, drawing, mindfulness break)  
- Allows the user to “change game” with a single click or voice command  
- Includes an “I’m bored” button to trigger an immediate activity change  

### 🎮 Entertainment & Gamification
- Features mini-educational games (memory, matching, mazes, spoken puzzles)  
- Reward system with stars, badges, or digital pets to feed and care for  
- Visual timer with animations to indicate when each activity ends  

### 📊 Data Tracking & Reporting
- Automatically logs:  
  - Attention span duration  
  - Game preferences  
  - Moments of frustration/relaxation  
  - Completed activities  
- Generates clear PDF or CSV reports for:  
  - Parents (via email)  
  - Teachers (via Google Drive or Teams)  
  - Healthcare providers (via app or portal)  
- Fully GDPR-compliant with explicit parental consent  

## 🛠️ Technologies Used

- **UI Framework**: Streamlit (Python)  
- **Speech Recognition**: Whisper (local)  
- **Text-to-Speech**: Coqui TTS (open-source)  
- **Activity Logic**: Custom Python “boredom” algorithm  
- **Gamification**: Local sprites and animations + JSON scoring  
- **Data Logging**: CSV + PDF/Excel generation  
- **Reporting**: WeasyPrint (PDF), pandas (CSV)  
- **External Connections (optional)**: Teams API / Email API  
- **Adult Dashboard (optional)**: Streamlit or Flask (local or cloud)  

## 🚀 Getting Started

1. Clone this repository  
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```  
3. Run the app:  
   ```bash
   streamlit run src/app.py
   ```

## 📁 Project Structure

```bash
flexibuddy/
├── src/
│   ├── app.py                   # Main child-facing UI
│   ├── voice_agent.py           # Whisper + Coqui TTS integration
│   ├── activity_switcher.py     # Activity-switching logic
│   ├── data_logger.py           # Interaction logging and progress tracking
│   ├── utils/
│       ├── __init__.py
│       ├── config.py            # Global configurations
│       ├── animations.py        # Animation handling
│       └── report_generator.py  # PDF/CSV report generation
├── assets/
│   ├── images/                  # Images and icons
│   ├── sounds/                  # Audio files
│   ├── games/                   # Game assets
│   └── fonts/                   # Custom fonts
├── data/
│   ├── logs/                    # Interaction logs
│   └── reports/                 # Generated reports
├── README.md
└── requirements.txt
```

## ⚠️ Requirements

- Python 3.8 or higher  
- Approximately 2 GB of disk space (for local AI models)  
- Microphone and speakers for voice interaction  
- Internet connection for initial installation (optional for runtime)  

## 📄 License

This project is released under the MIT open-source license.

## 🤝 Contributing

Contributions are welcome! To improve FlexiBuddy, feel free to fork the repository and submit a pull request. 

(Francesco Bulla 2025 – MIT License)