# init_real_data.py
from utils.database import init_database, import_kaggle_dataset
from utils.dataset_manager import DatasetManager
import os

def main():
    print("🧠 Initializing Brain Tumor Detection System...")
    
    # Step 1: Initialize database
    print("1. Initializing database...")
    init_database()
    
    # Step 2: Import Kaggle dataset
    print("2. Importing Kaggle dataset...")
    imported = import_kaggle_dataset()
    
    if imported == 0:
        print("⚠️ No data imported. Downloading dataset...")
        
        # Download dataset if not exists
        import kagglehub
        from pathlib import Path
        
        print("📥 Downloading dataset from Kaggle...")
        path = kagglehub.dataset_download("masoudnickparvar/brain-tumor-mri-dataset")
        print(f"✅ Downloaded to: {path}")
        
        # Try import again
        imported = import_kaggle_dataset(str(path))
    
    # Step 3: Show statistics
    print("3. Loading dataset statistics...")
    manager = DatasetManager()
    stats = manager.get_dataset_stats()
    
    print("\n" + "="*50)
    print("📊 DATABASE STATISTICS")
    print("="*50)
    print(f"Total cases: {stats['total_cases']}")
    print(f"Tumor cases: {stats['tumor_cases']}")
    print(f"Healthy cases: {stats['healthy_cases']}")
    print(f"Average confidence: {stats['avg_confidence']:.2%}")
    
    if 'stage_distribution' in stats:
        print("\nStage Distribution:")
        for stage, count in stats['stage_distribution'].items():
            print(f"  {stage}: {count} cases")
    
    print("\n✅ Initialization complete!")
    print(f"📁 Database: data/tumor_cases.db")
    print(f"🖼️ Dataset: data/dataset/")

if __name__ == "__main__":
    main()