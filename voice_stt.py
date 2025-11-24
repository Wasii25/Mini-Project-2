"""
Speech-to-Text Module using Vosk
Offline speech recognition
"""

import json
import pyaudio
from vosk import Model, KaldiRecognizer


class VoiceInput:
    """Handles offline speech-to-text using Vosk"""

    def __init__(self, model_path: str = "vosk-model-small-en-us-0.15"):
        """
        Initialize Vosk model

        Args:
            model_path: Path to downloaded Vosk model
        """
        print(f"Loading speech recognition model from {model_path}...")
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio = pyaudio.PyAudio()
        print("Speech recognition ready")

    def listen(self, timeout: int = 10) -> str:
        """
        Listen for speech and convert to text

        Args:
            timeout: Maximum seconds to listen

        Returns:
            Transcribed text or None if no speech detected
        """
        print("\nListening... (speak now)")

        stream = None
        try:
            # Open microphone stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000,
            )
            stream.start_stream()

            frames_read = 0
            max_frames = timeout * 2  # 16000 / 8000 = 2 frames per second

            while frames_read < max_frames:
                data = stream.read(4000, exception_on_overflow=False)
                frames_read += 1

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()

                    if text:
                        print(f"You said: {text}")
                        return text

            # Check partial result if nothing was finalized
            partial = json.loads(self.recognizer.FinalResult())
            text = partial.get("text", "").strip()

            if text:
                print(f"You said: {text}")
                return text
            else:
                print("No speech detected")
                return None

        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None

        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    def cleanup(self):
        """Clean up audio resources"""
        self.audio.terminate()
