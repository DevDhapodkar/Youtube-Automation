import asyncio
import edge_tts

TEXT = "This is a test of the emergency broadcast system."
VOICE = "en-US-JennyNeural"

async def test_tts():
    print(f"Testing voice: {VOICE}")
    communicate = edge_tts.Communicate(TEXT, VOICE)
    try:
        await communicate.save("test_output.mp3")
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tts())
