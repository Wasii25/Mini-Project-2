#!/usr/bin/env python3
"""
Voice-Enabled SQL Agent
Combines postgres_agent with voice input/output
"""

import asyncio
import sys
from db_agent import PostgresSQLAgent
from voice_stt import VoiceInput
from voice_tts import VoiceOutput


class VoiceSQLAgent:
    """SQL Agent with voice interface"""

    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        vosk_model_path: str = "vosk-model-small-en-us-0.15",
        tts_model: str = "tts_models/en/ljspeech/tacotron2-DDC",
    ):
        """
        Initialize voice-enabled agent

        Args:
            model_name: LLM model for SQL generation
            vosk_model_path: Path to Vosk STT model
            tts_model: Coqui TTS model name
        """
        print("Initializing Voice SQL Agent...")
        print("-" * 60)

        # Initialize SQL agent (without verbose output)
        self.sql_agent = PostgresSQLAgent(model_name=model_name, verbose=False)

        # Initialize voice modules
        self.voice_input = VoiceInput(model_path=vosk_model_path)
        self.voice_output = VoiceOutput(model_name=tts_model)

        print("-" * 60)
        print("Voice SQL Agent Ready!\n")

    async def run_voice_mode(self):
        """Run agent in voice mode"""

        # Connect to database
        await self.sql_agent.connect_mcp()

        # Welcome message

        try:
            while True:
                # Listen for question
                question = self.voice_input.listen(timeout=10)

                if not question:
                    retry_msg = "I didn't hear anything. Would you like to try again?"
                    print(retry_msg)
                    self.voice_output.speak(retry_msg)

                    retry_response = self.voice_input.listen(timeout=5)
                    if not retry_response or "no" in retry_response.lower():
                        break
                    continue

                # Check for exit
                if any(
                    word in question.lower()
                    for word in ["exit", "quit", "stop", "goodbye", "bye"]
                ):
                    farewell = "Goodbye!"
                    print(farewell)
                    self.voice_output.speak(farewell)
                    break

                # Process question
                print(f"\nProcessing: {question}")
                answer = await self.sql_agent.process_question(question, verbose=False)

                # Speak answer
                self.voice_output.speak(answer)

                print()  # Blank line for readability

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.sql_agent.disconnect_mcp()
            self.voice_input.cleanup()

    async def run_text_mode(self):
        """Run agent in text mode (fallback)"""
        await self.sql_agent.connect_mcp()
        await self.sql_agent.interactive_mode(verbose=False)


async def main():
    """Entry point"""

    # Check if voice mode is requested
    voice_mode = True

    if len(sys.argv) > 1 and sys.argv[1] == "--text":
        voice_mode = False

    agent = VoiceSQLAgent(
        model_name="llama3.2:3b",
        vosk_model_path="vosk-model-small-en-us-0.15",
        tts_model="tts_models/en/ljspeech/tacotron2-DDC",
    )

    if voice_mode:
        print("\n🎤 Starting in VOICE mode")
        print("Tip: Speak clearly and wait for the beep")
        print("Say 'exit' or 'goodbye' to quit\n")
        await agent.run_voice_mode()
    else:
        print("\n⌨️  Starting in TEXT mode")
        print("Type your questions\n")
        await agent.run_text_mode()


if __name__ == "__main__":
    asyncio.run(main())
