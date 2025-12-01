"""
Text input (no speech) - reliable and works
"""

import sys
import os


class VoiceInput:
    """Text input mode"""

    def __init__(self, model_path: str = None):
        print("Text input")

    def listen(self, timeout: int = 10) -> str:
        """Get text input"""
        try:
            text = input("\nYour question: ").strip()
            return text if text else None
        except:
            return None

    def cleanup(self):
        pass
