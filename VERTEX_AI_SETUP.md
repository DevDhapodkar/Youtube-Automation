# Vertex AI Authentication Setup

The gcloud CLI installation had issues. Here's a simpler approach using a service account:

## Steps to Set Up Authentication:

### 1. Create a Service Account
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts?project=youtube-agent-478611
2. Click "CREATE SERVICE ACCOUNT"
3. Name it: `youtube-agent-sa`
4. Click "CREATE AND CONTINUE"

### 2. Grant Permissions
Add these roles:
- **Vertex AI User** (for using Vertex AI services)
- **Storage Object Admin** (for storing generated images)

Click "CONTINUE" then "DONE"

### 3. Create and Download Key
1. Click on the service account you just created
2. Go to the "KEYS" tab
3. Click "ADD KEY" → "Create new key"
4. Choose "JSON" format
5. Click "CREATE" - a JSON file will download

### 4. Save the Key File
1. Move the downloaded JSON file to your project directory:
   ```bash
   mv ~/Downloads/youtube-agent-478611-*.json /Users/devdhapodkar/Desktop/ytagent/service-account-key.json
   ```

2. Add this line to your `.env` file:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/Users/devdhapodkar/Desktop/ytagent/service-account-key.json
   ```

### 5. Test Again
Run the test script:
```bash
./venv/bin/python test_vertex_ai.py
```

---

**Security Note:** Never commit the service account key file to git. It's already in `.gitignore`.
