#!/bin/bash

echo "🚀 Starting deployment setup..."

# Create necessary directories
mkdir -p data
mkdir -p uploads
mkdir -p includes
mkdir -p public

# Set permissions
chmod 755 data
chmod 755 uploads
chmod 755 includes

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Created .env file from example"
    fi
fi

# Create database directory with proper permissions
if [ ! -d "data" ]; then
    mkdir data
    chmod 755 data
fi

# Create uploads directory with proper permissions  
if [ ! -d "uploads" ]; then
    mkdir uploads
    chmod 755 uploads
fi

# Check if we're on Koyeb or Render
if [ ! -z "$PORT" ]; then
    echo "🌐 Detected cloud platform (PORT: $PORT)"
    # Cloud platform detected
    if [ ! -f "public/index.php" ]; then
        cat > public/index.php << 'EOF'
<?php
// Cloud platform entry point
require_once '../index.php';
?>
EOF
        echo "📁 Created cloud entry point"
    fi
fi

echo "✅ Deployment setup completed!"
