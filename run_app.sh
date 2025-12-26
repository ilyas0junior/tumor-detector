#!/bin/bash

# Brain Tumor Detector - Launch Script
echo "🧠 BRAIN TUMOR DETECTOR - Starting..."
echo "========================================"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
fi

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Setup database
echo "Setting up database..."
python setup_database.py

# Create sample images folder
mkdir -p sample_images

# Download a few sample images if folder is empty
if [ -z "$(ls -A sample_images 2>/dev/null)" ]; then
    echo "Downloading sample images..."
    cd sample_images
    curl -s -o brain_sample1.jpg "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/MRI_brain.jpg/400px-MRI_brain.jpg"
    curl -s -o brain_sample2.jpg "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Normal_posteroanterior_%28PA%29_chest_radiograph_%28X-ray%29.jpg/400px-Normal_posteroanterior_%28PA%29_chest_radiograph_%28X-ray%29.jpg"
    cd ..
fi

# Start the app
echo ""
echo "🚀 Starting Brain Tumor Detector..."
echo "App will open at: http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""
streamlit run tumor_app.py