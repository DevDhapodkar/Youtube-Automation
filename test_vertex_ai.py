#!/usr/bin/env python3
"""
Test script to verify Vertex AI setup and generate a test image.
"""
import os
from dotenv import load_dotenv
from vertexai.preview.vision_models import ImageGenerationModel

# Load environment variables
load_dotenv()

def test_vertex_ai():
    print("Testing Vertex AI setup...")
    
    # Check for project ID
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("\n❌ GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("\nPlease set it in your .env file:")
        print("GOOGLE_CLOUD_PROJECT=your-project-id")
        print("\nTo find your project ID:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Click the project dropdown at the top")
        print("3. Copy your project ID")
        return False
    
    print(f"✅ Project ID: {project_id}")
    
    # Try to initialize Vertex AI
    try:
        import vertexai
        vertexai.init(project=project_id, location="us-central1")
        print("✅ Vertex AI initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize Vertex AI: {e}")
        print("\nMake sure you have:")
        print("1. Enabled the Vertex AI API in your project")
        print("2. Set up authentication (gcloud auth application-default login)")
        return False
    
    # Try to generate a test image
    try:
        print("\n🎨 Generating test image...")
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        response = model.generate_images(
            prompt="A beautiful sunset over mountains",
            number_of_images=1,
            aspect_ratio="9:16",
        )
        
        if response.images:
            output_path = "test_vertex_image.png"
            response.images[0].save(output_path)
            print(f"✅ Test image generated successfully: {output_path}")
            print("\n🎉 Vertex AI is fully configured and working!")
            return True
        else:
            print("❌ No images returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Failed to generate image: {e}")
        print("\nThis might mean:")
        print("1. Vertex AI API is not enabled")
        print("2. You don't have proper permissions")
        print("3. Authentication is not set up correctly")
        return False

if __name__ == "__main__":
    test_vertex_ai()
