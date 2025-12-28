# utils/database.py - CLOUD COMPATIBLE VERSION
import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def get_db_path():
    """Get database path that works both locally and on cloud"""
    # Try different possible paths
    possible_paths = [
        'data/tumor_cases.db',           # Local development
        '/tmp/tumor_cases.db',           # Cloud temp directory
        'tumor_cases.db',                # Current directory
        os.path.join(os.path.dirname(__file__), '../data/tumor_cases.db')
    ]
    
    for path in possible_paths:
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            # Try to connect
            test_conn = sqlite3.connect(path)
            test_conn.close()
            return path
        except:
            continue
    
    # Default to current directory
    return 'tumor_cases.db'

def init_database():
    """Initialize database for cloud"""
    db_path = get_db_path()
    
    # Create directory if needed
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
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
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add demo data if table is empty
    c.execute("SELECT COUNT(*) FROM cases")
    count = c.fetchone()[0]
    
    if count == 0:
        demo_cases = [
            ('CLOUD_001', 'Stage II', 0.85, 1, '2.3 cm', 'Moderate', 'Brain', datetime.now()),
            ('CLOUD_002', 'Stage I', 0.92, 1, '1.5 cm', 'Low', 'Brain', datetime.now()),
            ('CLOUD_003', 'Stage III', 0.78, 2, '3.8 cm', 'High', 'Brain', datetime.now()),
            ('CLOUD_004', 'No tumor', 0.95, 0, '0 cm', 'None', 'Brain', datetime.now())
        ]
        
        for case in demo_cases:
            c.execute('''
                INSERT INTO cases (case_id, stage, confidence, tumor_count, tumor_size, malignancy, location, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', case)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {db_path}")

def get_all_cases():
    """Get all cases from database"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    try:
        df = pd.read_sql_query("SELECT * FROM cases ORDER BY uploaded_at DESC", conn)
    except:
        # If error, return empty dataframe
        df = pd.DataFrame()
    
    conn.close()
    return df

def save_case(analysis_result, case_id=None):
    """Save analysis to database"""
    if case_id is None:
        case_id = f"CLOUD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO cases 
            (case_id, stage, confidence, tumor_count, tumor_size, malignancy, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_id,
            analysis_result.get('stage', 'Unknown'),
            analysis_result.get('confidence', 0),
            analysis_result.get('tumor_count', 0),
            analysis_result.get('size', 'N/A'),
            analysis_result.get('malignancy', 'Unknown'),
            analysis_result.get('location', 'Unknown')
        ))
        
        conn.commit()
        return case_id
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_statistics():
    """Get statistics for dashboard"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    stats = {
        'total_cases': 0,
        'stage_distribution': {},
        'avg_confidence': 0
    }
    
    try:
        c = conn.cursor()
        
        # Total cases
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
        print(f"Statistics error: {e}")
    finally:
        conn.close()
    
    return stats

# Other functions remain similar, just use get_db_path()