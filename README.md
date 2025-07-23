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
          username: <your_username>
          password: ${{ secrets.DOCKER_PASSWORD }}
          project: 'my-app'
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
        uses: michielvha/docker-release-action@v1
        with:
          username: <your_username>
          password: ${{ secrets.DOCKER_PASSWORD }}
          project: 'my-app'
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
  uses: michielvha/gitversion-tag-action@v5
  with:
    configFilePath: 'gitversion.yml'
```

### 3. GitVersion Configuration

Create a `gitversion.yml` file in your repository root:

```yaml
# https://gitversion.net/docs/reference/configuration
# manually verify with `gitversion (/showconfig)`
# IMPORTANT: on initial onboarding comment out everything but workflow after first run you can put it back
workflow: GitHubFlow/v1
# Custom strategies - this differs from default

strategies:
  - MergeMessage
  - TaggedCommit
  - TrackReleaseBranches
  - VersionInBranchName
branches:
  main:
    regex: ^master$|^main$
    increment: Patch
    prevent-increment:
      of-merged-branch: true
    track-merge-target: false
    track-merge-message: true
    is-main-branch: true
    mode: ContinuousDeployment # also do it here
  release:
    # Custom release branch configuration
    regex: ^release/(?<BranchName>[0-9]+\.[0-9]+\.[0-9]+)$
    label: ''
    increment: None
    prevent-increment:
      when-current-commit-tagged: true
      of-merged-branch: true
    is-release-branch: true
    mode: ContinuousDeployment # do not use ContinuousDelivery, else it will increment the version with a suffix on each commit.
    source-branches:
      - main
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
