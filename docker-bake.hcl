# Docker Bake configuration for Gukas AI Agent
# Enables advanced BuildKit features and multi-platform builds

variable "TAG" {
  default = "latest"
}

variable "REGISTRY" {
  default = "gukas"
}

# Default group - builds all targets
group "default" {
  targets = ["gukas-agent"]
}

# Development group - includes dev tools
group "dev" {
  targets = ["gukas-agent-dev"]
}

# Production target
target "gukas-agent" {
  dockerfile = "Dockerfile"
  target = "production"
  tags = [
    "${REGISTRY}/gukas-ai-agent:${TAG}",
    "${REGISTRY}/gukas-ai-agent:latest"
  ]
  platforms = ["linux/amd64", "linux/arm64"]
  
  # BuildKit cache configuration
  cache-from = [
    "type=gha",
    "type=registry,ref=${REGISTRY}/gukas-ai-agent:cache"
  ]
  cache-to = [
    "type=gha,mode=max",
    "type=registry,ref=${REGISTRY}/gukas-ai-agent:cache,mode=max"
  ]
  
  # Build arguments
  args = {
    BUILDKIT_INLINE_CACHE = "1"
  }
  
  # Labels
  labels = {
    "org.opencontainers.image.title" = "Gukas AI Agent"
    "org.opencontainers.image.description" = "AI-powered coffee farming assistant"
    "org.opencontainers.image.version" = "${TAG}"
    "org.opencontainers.image.created" = "${timestamp()}"
  }
}

# Development target with additional tools
target "gukas-agent-dev" {
  inherits = ["gukas-agent"]
  target = "builder"
  tags = [
    "${REGISTRY}/gukas-ai-agent:dev-${TAG}",
    "${REGISTRY}/gukas-ai-agent:dev-latest"
  ]
  
  # Development-specific args
  args = {
    BUILDKIT_INLINE_CACHE = "1"
    DEBUG = "true"
  }
}

# Local development target
target "local" {
  inherits = ["gukas-agent"]
  tags = ["gukas-ai-agent:local"]
  platforms = ["linux/amd64"]
  output = ["type=docker"]
}