from gradio_client import Client

def inspect():
    try:
        client = Client("ali-vilab/modelscope-damo-text-to-video-synthesis")
        client.view_api()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
