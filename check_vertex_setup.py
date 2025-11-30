#!/usr/bin/env python3
"""
Check service account permissions and API status
"""
import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import aiplatform

load_dotenv()

def check_setup():
    # Check if credentials file exists
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    print(f"✅ Credentials file found: {creds_path}")
    
    # Load and check credentials
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        print(f"✅ Service account email: {creds_data.get('client_email')}")
        print(f"✅ Project ID: {creds_data.get('project_id')}")
        
        # Try to create credentials
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        print("✅ Credentials loaded successfully")
        
        # Try to initialize Vertex AI
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        aiplatform.init(
            project=project_id,
            location='us-central1',
            credentials=credentials
        )
        print("✅ Vertex AI initialized with credentials")
        
        print("\n🎉 Setup looks good!")
        print("\nNext: Make sure these APIs are enabled in your project:")
        print(f"https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={project_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_setup()
