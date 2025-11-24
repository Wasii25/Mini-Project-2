"""
Text-to-Speech Module using pyttsx3
Offline TTS (no large downloads, works on Python 3.12)
"""

import pyttsx3


class VoiceOutput:
    """Offline text-to-speech using pyttsx3"""

    def __init__(self):
        print("Initializing offline TTS (pyttsx3)...")
        self.engine = pyttsx3.init()

        # Optional tuning
        rate = self.engine.getProperty("rate")
        self.engine.setProperty("rate", int(rate * 0.95))  # slightly slower

        voices = self.engine.getProperty("voices")
        if voices:
            self.engine.setProperty("voice", voices[0].id)

        print("Text-to-speech ready")

    def speak(self, text: str, blocking: bool = True):
        if not text or not text.strip():
            return

        print(f"Speaking: {text[:50]}..." if len(text) > 50 else f"Speaking: {text}")

        try:
            self.engine.say(text)
            if blocking:
                self.engine.runAndWait()
        except Exception as e:
            print(f"Error during TTS: {e}")
            print(f"Fallback (text): {text}")

    def speak_async(self, text: str):
        """Speak without blocking the main thread."""
        self.speak(text, blocking=False)
