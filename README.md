# Docker Release Action

A reusable GitHub Action that builds and publishes Docker images with automatic version detection from GitVersion environment variables.

## Features

- 🐳 Docker image building and pushing to Docker Hub
- 🏗️ Multi-platform support (configurable)
- 🔄 Reusable across multiple repositories
- 🏷️ Automatic tagging with version, latest, and SHA
- ⚡ Simple and clean - no complex configuration needed
- 🎯 Works seamlessly with GitVersion environment variables

## How It Works

This action automatically uses the `GITVERSION_SEMVER` environment variable set by GitVersion tools and creates three Docker tags:
- **Version tag**: `username/project:1.2.3`
- **Latest tag**: `username/project:latest`  
- **SHA tag**: `username/project:abc123...`

## Usage

### Basic Example

```yaml
name: Build and Release

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Tag with GitVersion
        uses: michielvha/gitversion-tag-action@v3
        with:
          configFilePath: 'gitversion.yml'

      - name: Build and Push Docker Image
        uses: michielvha/release-action@v1
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
          Project: 'my-app'
```

### Advanced Example

```yaml
name: Build and Release

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Tag with GitVersion
        uses: michielvha/gitversion-tag-action@v3
        with:
          configFilePath: 'gitversion.yml'

      - name: Build and Push Docker Image
        id: docker-build
        uses: michielvha/release-action@v1
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
          Project: 'my-app'
          platforms: 'linux/amd64,linux/arm64'
          context: './src'
      
      - name: Display image digest
        run: |
          echo "Image digest: ${{ steps.docker-build.outputs.image-digest }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `username` | Docker Hub username | ✅ | - |
| `password` | Docker Hub password or token | ✅ | - |
| `Project` | Project name for Docker image | ✅ | - |
| `platforms` | Target platforms for Docker build | ❌ | `linux/amd64` |
| `context` | Docker build context | ❌ | `.` |

## Outputs

| Output | Description |
|--------|-------------|
| `image-digest` | Docker image digest |

## Generated Tags

This action automatically generates the following Docker tags:

1. **Version Tag**: `{username}/{Project}:{GITVERSION_SEMVER}`
2. **Latest Tag**: `{username}/{Project}:latest`
3. **SHA Tag**: `{username}/{Project}:{github.sha}`

## Prerequisites

### 1. Docker Hub Secrets

Add these secrets to your repository:

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

### 2. GitVersion Setup

Use this action with GitVersion to automatically set the `GITVERSION_SEMVER` environment variable:

```yaml
- name: Tag with GitVersion
  uses: michielvha/gitversion-tag-action@v3
  with:
    configFilePath: 'gitversion.yml'
```

### 3. GitVersion Configuration

Create a `gitversion.yml` file in your repository root:

```yaml
mode: MainLine
branches:
  main:
    regex: ^main$
    increment: Minor
    prevent-increment-of-merged-branch-version: true
    tag: ''
    track-merge-target: false
    tracks-release-branches: false
    is-release-branch: true
  feature:
    regex: ^features?[/-]
    increment: Minor
    prevent-increment-of-merged-branch-version: false
    tag: 'feat'
    track-merge-target: false
    tracks-release-branches: false
    is-release-branch: false
ignore:
  sha: []
merge-message-formats: {}
```

### 4. Repository Permissions

Ensure your workflow has the required permissions:

```yaml
permissions:
  contents: write  # For GitVersion tagging
```

## Dependencies

This action uses the following third-party actions:

- `docker/login-action@v3`
- `docker/setup-buildx-action@v3`
- `docker/build-push-action@v5`

## Example Repository Structure

```
your-repo/
├── .github/
│   └── workflows/
│       └── release.yml
├── src/
│   └── Dockerfile
├── gitversion.yml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/michielvha/release-action/issues).
