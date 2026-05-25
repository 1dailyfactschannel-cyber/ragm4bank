#!/bin/bash
# Ollama initialization script - downloads required models

echo "Initializing Ollama models..."

# Pull embedding model
echo "Pulling nomic-embed-text model..."
curl http://localhost:11434/api/pull -d '{
  "name": "nomic-embed-text"
}'

# Pull LLM model
echo "Pulling qwen2.5:7b model..."
curl http://localhost:11434/api/pull -d '{
  "name": "qwen2.5:7b"
}'

echo "Ollama initialization complete!"
echo "Available models:"
curl http://localhost:11434/api/tags
