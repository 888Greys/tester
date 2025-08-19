#!/bin/bash

echo "🔍 SSH Key Format Checker"
echo "=========================="

KEY_FILE="$HOME/.ssh/github_actions_key"

if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found: $KEY_FILE"
    exit 1
fi

echo "✅ Key file found: $KEY_FILE"
echo ""

echo "📊 Key Statistics:"
echo "- File size: $(wc -c < "$KEY_FILE") bytes"
echo "- Line count: $(wc -l < "$KEY_FILE") lines"
echo "- File permissions: $(ls -l "$KEY_FILE" | awk '{print $1}')"
echo ""

echo "🔍 Key Format Check:"
if ssh-keygen -l -f "$KEY_FILE" >/dev/null 2>&1; then
    echo "✅ Key format is valid"
    ssh-keygen -l -f "$KEY_FILE"
else
    echo "❌ Key format is invalid"
fi
echo ""

echo "📋 Key Content (first and last lines):"
echo "First line: $(head -n 1 "$KEY_FILE")"
echo "Last line: $(tail -n 1 "$KEY_FILE")"
echo ""

echo "🔍 Checking for problematic characters:"
if grep -q $'\r' "$KEY_FILE"; then
    echo "❌ Found carriage returns (\\r) - this will cause issues"
else
    echo "✅ No carriage returns found"
fi

if [[ $(tail -c 1 "$KEY_FILE" | wc -l) -eq 0 ]]; then
    echo "❌ Missing final newline"
else
    echo "✅ Proper final newline"
fi
echo ""

echo "🧪 SSH Connection Test:"
if ssh -i "$KEY_FILE" -o ConnectTimeout=5 -o StrictHostKeyChecking=no mathew@5.189.131.103 "echo 'Local SSH test successful'" 2>/dev/null; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
fi
echo ""

echo "📋 Ready for GitHub Secret:"
echo "Copy this EXACT content to GitHub SSH_PRIVATE_KEY secret:"
echo "================================================="
cat "$KEY_FILE"
echo "================================================="
echo ""

echo "🎯 Instructions:"
echo "1. Copy the content between the ===== lines above"
echo "2. Go to: https://github.com/Brand-Design-Development/gukas-ml/settings/secrets/actions"
echo "3. Update SSH_PRIVATE_KEY secret with the copied content"
echo "4. Make sure there are no extra spaces or characters"
echo "5. Test the workflow again"
