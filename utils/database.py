# utils/database.py
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime
import os
from pathlib import Path

def init_database():
    """Initialize SQLite database"""
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect('data/tumor_cases.db')
    c = conn.cursor()
    
    # Cases table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE,
            stage TEXT,
            confidence REAL,
            tumor_count INTEGER,
            tumor_size TEXT,
            malignancy TEXT,
            location TEXT,
            uploaded_at TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    # Similar cases table
    c.execute('''
        CREATE TABLE IF NOT EXISTS similar_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_case_id TEXT,
            similar_case_id TEXT,
            similarity_score REAL,
            match_reason TEXT
        )
    ''')
    
    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_stage ON cases(stage)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_location ON cases(location)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_uploaded ON cases(uploaded_at)')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized: data/tumor_cases.db")
    return True

def import_kaggle_dataset(dataset_path="data/dataset"):
    """Import Kaggle dataset into database"""
    dataset_dir = Path(dataset_path)
    
    if not dataset_dir.exists():
        print(f"❌ Dataset not found at {dataset_path}")
        return 0
    
    conn = sqlite3.connect('data/tumor_cases.db')
    c = conn.cursor()
    
    imported = 0
    categories = {
        'glioma': 'Glioma Tumor',
        'meningioma': 'Meningioma Tumor',
        'pituitary': 'Pituitary Tumor',
        'notumor': 'No Tumor'
    }
    
    for category, category_name in categories.items():
        category_path = dataset_dir / category
        
        if not category_path.exists():
            continue
        
        for image_file in category_path.glob("*.jpg"):
            try:
                # Generate unique case ID
                case_id = f"KGL_{category}_{image_file.stem}"
                
                # Check if already exists
                c.execute("SELECT 1 FROM cases WHERE case_id = ?", (case_id,))
                if c.fetchone():
                    continue  # Skip if already exists
                
                # Determine stage based on category
                if category == 'notumor':
                    stage = "No tumor"
                    confidence = 0.95
                    malignancy = "None"
                    tumor_count = 0
                else:
                    # For tumors, assign random stage for demo
                    stages = ['Stage I', 'Stage II', 'Stage III']
                    stage = np.random.choice(stages, p=[0.5, 0.3, 0.2])
                    confidence = np.random.uniform(0.7, 0.9)
                    malignancy = np.random.choice(['Low', 'Moderate', 'High'])
                    tumor_count = 1
                
                # Insert into database
                c.execute('''
                    INSERT INTO cases 
                    (case_id, stage, confidence, tumor_count, tumor_size, malignancy, location, uploaded_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    case_id,
                    stage,
                    confidence,
                    tumor_count,
                    f"{np.random.uniform(1.0, 4.0):.1f} cm",
                    malignancy,
                    "Brain",
                    datetime.now(),
                    json.dumps({
                        'source': 'kaggle',
                        'category': category,
                        'filename': image_file.name,
                        'path': str(image_file),
                        'type': 'MRI',
                        'description': category_name
                    })
                ))
                
                imported += 1
                
                # Print progress every 100 images
                if imported % 100 == 0:
                    print(f"  Imported {imported} images...")
                
            except Exception as e:
                print(f"Error importing {image_file}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Imported {imported} cases from Kaggle dataset")
    return imported

def save_case(analysis_result, case_id=None):
    """Save analysis to database"""
    if case_id is None:
        case_id = f"USER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    conn = sqlite3.connect('data/tumor_cases.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT OR REPLACE INTO cases 
            (case_id, stage, confidence, tumor_count, tumor_size, malignancy, location, uploaded_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_id,
            analysis_result.get('stage'),
            analysis_result.get('confidence'),
            analysis_result.get('tumor_count', 0),
            analysis_result.get('largest_size', 'N/A'),
            analysis_result.get('malignancy', 'Unknown'),
            analysis_result.get('location', 'Unknown'),
            datetime.now(),
            json.dumps(analysis_result)
        ))
        
        conn.commit()
        return case_id
    except Exception as e:
        print(f"Error saving case: {e}")
        return None
    finally:
        conn.close()

def get_similar_cases(stage, location, limit=3):
    """Get similar cases from database"""
    conn = sqlite3.connect('data/tumor_cases.db')
    
    query = '''
        SELECT * FROM cases 
        WHERE stage = ? AND location LIKE ?
        ORDER BY RANDOM()
        LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=(stage, f"%{location}%", limit))
    conn.close()
    
    return df

def get_all_cases():
    """Get all cases for dashboard"""
    conn = sqlite3.connect('data/tumor_cases.db')
    df = pd.read_sql_query("SELECT * FROM cases ORDER BY uploaded_at DESC", conn)
    conn.close()
    return df

def get_statistics():
    """Get statistics for dashboard"""
    conn = sqlite3.connect('data/tumor_cases.db')
    
    stats = {
        'total_cases': 0,
        'stage_distribution': {},
        'avg_confidence': 0
    }
    
    try:
        # Total cases
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM cases")
        stats['total_cases'] = c.fetchone()[0]
        
        # Stage distribution
        c.execute("SELECT stage, COUNT(*) FROM cases GROUP BY stage")
        for stage, count in c.fetchall():
            stats['stage_distribution'][stage] = count
        
        # Average confidence
        c.execute("SELECT AVG(confidence) FROM cases")
        avg_conf = c.fetchone()[0]
        stats['avg_confidence'] = avg_conf if avg_conf else 0
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
    finally:
        conn.close()
    
    return stats

def clear_database():
    """Clear all data from database (careful!)"""
    conn = sqlite3.connect('data/tumor_cases.db')
    c = conn.cursor()
    c.execute("DELETE FROM cases")
    c.execute("DELETE FROM similar_cases")
    conn.commit()
    conn.close()
    print("🗑️ Database cleared")
    return True