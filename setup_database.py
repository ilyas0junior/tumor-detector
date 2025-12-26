# setup_database.py - SIMPLIFIED
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧠 Setting up Brain Tumor Detector...")
print("="*50)

# Import after path setup
try:
    from utils.database import init_database, import_kaggle_dataset
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    init_database()
    
    # Step 2: Try to import dataset
    print("\n2. Checking for dataset...")
    dataset_path = Path("data/dataset")
    
    if dataset_path.exists():
        print(f"   Found dataset at: {dataset_path}")
        imported = import_kaggle_dataset(str(dataset_path))
        print(f"   ✅ Imported {imported} cases")
    else:
        print("   ℹ️ Dataset not found. Using demo mode.")
        print("   To use real data, download from Kaggle:")
        print("   kaggle datasets download masoudnickparvar/brain-tumor-mri-dataset")
    
    print("\n" + "="*50)
    print("✅ SETUP COMPLETE!")
    print("📁 Database: data/tumor_cases.db")
    print("🎯 Run: streamlit run tumor_app.py")
    print("="*50)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all files are in place.")
except Exception as e:
    print(f"❌ Setup error: {e}")