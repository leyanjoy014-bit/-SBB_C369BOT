import json
import os

# Global variable to store topics
topics = {}
TOPICS_FILE = 'topics.json'

def load_topics():
    """Load topics from JSON file."""
    global topics
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r') as f:
                topics = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            topics = {}
    else:
        topics = {}

def save_topics():
    """Save topics to JSON file."""
    with open(TOPICS_FILE, 'w') as f:
        json.dump(topics, f, indent=2)
