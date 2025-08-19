# SSH Key Setup Guide for GitHub Actions

## Current Issue: `error in libcrypto`

The error you're seeing indicates an SSH key format or encoding issue. Here's how to fix it:

## ✅ **SOLUTION COMPLETED**

**Status**: SSH key successfully generated and installed!

### Generated Key Details:
- **Key Type**: Ed25519 (modern, secure)
- **Key File**: `~/.ssh/github_actions_key`
- **Server**: `mathew@5.189.131.103`
- **Status**: ✅ Key added to server successfully

### Private Key for GitHub Secret:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCieAnUN+WLHIO6JRj9/glQTz1JKjKtxMu70xU7svYgVAAAAKg7B6+kOwev
pAAAAAtzc2gtZWQyNTUxOQAAACCieAnUN+WLHIO6JRj9/glQTz1JKjKtxMu70xU7svYgVA
AAAEB0gjcbAXmROeg/9eFKTHz4ssipUsqdAFe1FA4PXpCLWaJ4CdQ35Yscg7olGP3+CVBP
PUkqMq3Ey7vTFTuy9iBUAAAAHnBvbXBvbXB1cmluQE1hdGhld3MtaU1hYy5sb2NhbAECAw
QFBgc=
-----END OPENSSH PRIVATE KEY-----
```

### Next Steps:
1. **Update GitHub Secret**: Copy the above private key to `SSH_PRIVATE_KEY` secret
2. **Verify SERVER_IP**: Ensure it's set to `5.189.131.103`
3. **Run test workflow**: Use `test-ssh.yml` to verify connection
4. **Deploy**: Run the main deployment workflow

---

## 🔍 **Diagnosing the Problem**

The error `Error loading key "(stdin)": error in libcrypto` typically means:
1. **Wrong key format** - Key might be in wrong encoding
2. **Encrypted key** - Key has a passphrase (not supported in GitHub Actions)
3. **Corrupted key** - Key content is incomplete or malformed
4. **Wrong key type** - Using unsupported key algorithm

## 🔧 **Solution Steps**

### Step 1: Generate a New SSH Key (Recommended)

```bash
# Generate a new SSH key without passphrase
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions_key -N ""

# Or use Ed25519 (more modern, smaller)
ssh-keygen -t ed25519 -f ~/.ssh/github_actions_key -N ""
```

### Step 2: Add Public Key to Server

```bash
# Copy public key to server
ssh-copy-id -i ~/.ssh/github_actions_key.pub mathew@YOUR_SERVER_IP

# Or manually add to server's ~/.ssh/authorized_keys
cat ~/.ssh/github_actions_key.pub | ssh mathew@YOUR_SERVER_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Step 3: Add Private Key to GitHub Secrets

```bash
# Display private key content (copy this)
cat ~/.ssh/github_actions_key
```

**Important:** Copy the **entire** key including:
- `-----BEGIN OPENSSH PRIVATE KEY-----`
- All the content in between
- `-----END OPENSSH PRIVATE KEY-----`

### Step 4: Update GitHub Repository Secrets

1. Go to your repository: `https://github.com/Brand-Design-Development/gukas-ml`
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Update `SSH_PRIVATE_KEY` with the new private key content
4. Ensure `SERVER_IP` is set correctly

## 🚨 **Common Mistakes to Avoid**

### ❌ Wrong Key Format
```
# Don't use keys that start with:
ssh-rsa AAAAB3NzaC1yc2EAAAA...  # This is a PUBLIC key

# Don't use PEM format:
-----BEGIN RSA PRIVATE KEY-----  # Old PEM format
```

### ✅ Correct Key Format
```
# Use keys that start with:
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn...
-----END OPENSSH PRIVATE KEY-----
```

### ❌ Encrypted Keys
```bash
# Don't use keys with passphrases
ssh-keygen -t rsa -b 4096 -f key -P "mypassword"  # ❌ Has passphrase
```

### ✅ Unencrypted Keys
```bash
# Use keys without passphrases
ssh-keygen -t rsa -b 4096 -f key -N ""  # ✅ No passphrase
```

## 🔬 **Testing Your SSH Key**

### Test 1: Local SSH Connection
```bash
# Test SSH connection from your local machine
ssh -i ~/.ssh/github_actions_key mathew@YOUR_SERVER_IP "echo 'SSH works!'"
```

### Test 2: Key Format Validation
```bash
# Check if key format is valid
ssh-keygen -l -f ~/.ssh/github_actions_key
# Should show: "4096 SHA256:abc123... comment (RSA)" or similar
```

### Test 3: GitHub Actions Workflow
The updated workflow now includes diagnostics that will show:
- SSH agent status
- Connection test results
- Key format validation
- Fallback SSH method if needed

## 🛠️ **Alternative Solutions**

### Option 1: Use Password Authentication (Less Secure)
```yaml
- name: Deploy via password
  uses: appleboy/ssh-action@v0.1.7
  with:
    host: ${{ secrets.SERVER_IP }}
    username: mathew
    password: ${{ secrets.SERVER_PASSWORD }}
    script: |
      # deployment commands here
```

### Option 2: Use Different SSH Action
```yaml
- name: Deploy via different SSH action
  uses: appleboy/ssh-action@v0.1.7
  with:
    host: ${{ secrets.SERVER_IP }}
    username: mathew
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      # deployment commands here
```

## 📋 **Verification Checklist**

- [ ] Generated new SSH key without passphrase
- [ ] Added public key to server's authorized_keys
- [ ] Copied **entire** private key to GitHub secret
- [ ] Key starts with `-----BEGIN OPENSSH PRIVATE KEY-----`
- [ ] Key ends with `-----END OPENSSH PRIVATE KEY-----`
- [ ] No line breaks or extra characters in the secret
- [ ] Can SSH to server manually with the key

## 🔄 **Next Steps**

1. **Generate new SSH key** following the steps above
2. **Test locally** that the key works
3. **Update GitHub secret** with the new private key
4. **Run the workflow** - it will now show diagnostics
5. **Check the logs** for SSH connection status

The workflow will now provide detailed diagnostics to help identify exactly what's wrong with the SSH setup!
