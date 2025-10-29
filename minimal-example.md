name: Build and Release

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v5

      - name: Build and Push Docker Image
        uses: michielvha/docker-release-action@main
        with:
          username: <your_username>
          password: ${{ secrets.DOCKER_PASSWORD }}
          project: 'my-app'
          version: '1.2.3'  # Or omit to use 'dev' default
