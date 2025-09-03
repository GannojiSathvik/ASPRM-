#!/bin/bash

echo "🚀 Step 1: Sending a test security finding..."

# FIX 1: The JSON payload now correctly matches the WebhookPayload model.
curl -X POST http://127.0.0.1:8000/webhook/semgrep -H "Content-Type: application/json" -d '{
  "results": [
    {
      "check_id": "generic.secrets.security.hardcoded-secret.hardcoded-value",
      "path": "app/settings.py",
      "start": { "line": 50 },
      "extra": {
        "fingerprint": "test_fingerprint_123",
        "lines": "DATABASE_PASSWORD = \"SuperSecretPassword123!\"",
        "message": "Hardcoded secret detected in settings file.",
        "severity": "ERROR",
        "metadata": {}
      }
    }
  ],
  "repo_name": "my-test/repo",
  "commit": "HEAD"
}'

# Adding a newline for cleaner output
echo ""
echo ""

# Wait for the server to process the request
sleep 2

echo "🧠 Step 2: Asking the AI for an explanation..."

# FIX 2: Added -X POST to use the correct HTTP method.
curl -X POST http://127.0.0.1:8000/risks/test_fingerprint_123/explain

# Adding a newline for cleaner output
echo ""
echo ""

echo "✅ Test complete."