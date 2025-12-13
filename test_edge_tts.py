import asyncio
import edge_tts
import os

async def test_edge_tts():
    text = "This is a test of edge TTS audio generation."
    voice = "en-US-AriaNeural"
    output_file = "test_edge_tts.mp3"
    
    print(f"Testing edge-tts with voice: {voice}")
    
    communicate = edge_tts.Communicate(text, voice)
    
    audio_chunks = 0
    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
                audio_chunks += 1
    
    print(f"Audio chunks written: {audio_chunks}")
    
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"Output file created: {output_file} ({size} bytes)")
        return True
    else:
        print("Output file not created!")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_edge_tts())
    print(f"Test result: {'SUCCESS' if result else 'FAILED'}")
