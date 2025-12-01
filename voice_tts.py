import pyttsx3


class VoiceOutput:
    """Handles text-to-speech"""

    def __init__(self, model_name: str = None):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 0.9)
        print("Text-to-speech ready")

    def speak(self, text: str, blocking: bool = True):
        """Convert text to speech"""
        if not text:
            return
        print(f"Speaking: {text}")
        self.engine.say(text)
        if blocking:
            self.engine.runAndWait()

    def speak_async(self, text: str):
        self.speak(text, blocking=False)
