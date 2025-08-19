# GitHub Actions Setup Requirements

## Required Repository Secrets

To enable the CI/CD pipeline for Guka AI Agent, configure these secrets in the repository settings:

### Authentication & API Keys
- `CEREBRAS_API_KEY` - Your Cerebras AI API key for the LLM service
- `DJANGO_BASE_URL` - Base URL of your Django backend (e.g., https://api.yourdomain.com)
- `DJANGO_API_TOKEN` - API token for Django backend authentication
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions (no configuration needed)

### Deployment Secrets
- `SSH_PRIVATE_KEY` - SSH private key for server access
- `SERVER_IP` - IP address of your production server
- `DOMAIN_NAME` - Your production domain name (e.g., agent.yourdomain.com)

### Optional Docker Hub Fallback
- `DOCKERHUB_USERNAME` - Docker Hub username (if GHCR fails)
- `DOCKERHUB_TOKEN` - Docker Hub access token (if GHCR fails)

## GitHub Container Registry (GHCR) Setup

### Organization Settings Required:
1. Go to your GitHub organization settings
2. Navigate to "Packages" section
3. Enable "Package creation" for repository members
4. Set package visibility to allow public or private packages as needed

### Repository Permissions:
The workflow requires these permissions:
- `contents: read` - To checkout code
- `packages: write` - To push Docker images to GHCR
- `id-token: write` - For OIDC authentication

### Common GHCR Issues:

#### 403 Forbidden Error
This usually means:
- Organization hasn't enabled package creation for repositories
- Repository doesn't have packages permission enabled
- User doesn't have write access to the packages

**Fix**: Contact organization admin to enable package creation in organization settings.

#### Package Naming
- GHCR requires lowercase names: `ghcr.io/org-name/package-name`
- Repository names with uppercase letters will fail
- Use explicit lowercase names in workflow

## Workflow Files

### Main Deployment: `.github/workflows/deploy.yml`
- Builds and tests the application
- Pushes Docker image to GHCR
- Deploys to production server via SSH

### Test GHCR Access: `.github/workflows/test-ghcr.yml`
- Tests if repository can push to GitHub Container Registry
- Useful for debugging permissions issues
- Runs on `workflow_dispatch` (manual trigger)

## Alternative: Docker Hub Registry

If GHCR continues to fail, you can switch to Docker Hub:

```yaml
env:
  REGISTRY: docker.io
  IMAGE_NAME: yourusername/guka-agent
```

And update the login step:
```yaml
- name: 🔑 Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

## Testing the Setup

1. Push any change to trigger the workflow
2. Check GitHub Actions tab for build results
3. For GHCR issues, run the test workflow manually:
   - Go to Actions → Test GHCR Access → Run workflow

## Troubleshooting

### Disk Space Issues
The workflow includes aggressive cleanup steps:
- Removes unnecessary software packages
- Cleans Docker cache
- Optimized for GitHub's 14GB runner limit

### SSH Connection Issues
- Ensure SSH key has proper permissions on server
- Server must allow SSH key authentication
- Use `StrictHostKeyChecking=no` for automated deployments

### Health Check Failures
- Service takes ~30 seconds to start
- Health endpoint: `http://localhost:8001/health`
- Check container logs: `docker logs gukas-ai-agent --tail 20`
