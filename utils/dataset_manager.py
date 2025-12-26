# utils/dataset_manager.py
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from PIL import Image
import streamlit as st

class DatasetManager:
    def __init__(self, db_path='data/tumor_cases.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_dataset_stats(self):
        """Get statistics about the dataset"""
        conn = self.connect()
        
        query = """
        SELECT 
            COUNT(*) as total_cases,
            SUM(CASE WHEN stage LIKE 'Stage%' THEN 1 ELSE 0 END) as tumor_cases,
            SUM(CASE WHEN stage = 'No tumor' THEN 1 ELSE 0 END) as healthy_cases,
            AVG(confidence) as avg_confidence
        FROM cases
        WHERE metadata LIKE '%kaggle%'
        """
        
        stats = pd.read_sql_query(query, conn).iloc[0].to_dict()
        
        # Get stage distribution
        stage_query = """
        SELECT stage, COUNT(*) as count
        FROM cases 
        WHERE metadata LIKE '%kaggle%' AND stage LIKE 'Stage%'
        GROUP BY stage
        ORDER BY stage
        """
        
        stage_df = pd.read_sql_query(stage_query, conn)
        stats['stage_distribution'] = stage_df.set_index('stage')['count'].to_dict()
        
        self.close()
        return stats
    
    def get_similar_real_cases(self, stage, location="Brain", limit=5):
        """Get similar real cases from Kaggle dataset"""
        conn = self.connect()
        
        query = """
        SELECT * FROM cases 
        WHERE metadata LIKE '%kaggle%' 
        AND location = ? 
        AND stage = ?
        ORDER BY RANDOM()
        LIMIT ?
        """
        
        cases = pd.read_sql_query(query, conn, params=(location, stage, limit))
        self.close()
        
        return cases
    
    def get_case_image(self, case_id):
        """Get image for a specific case"""
        conn = self.connect()
        c = conn.cursor()
        
        c.execute("SELECT metadata FROM cases WHERE case_id = ?", (case_id,))
        result = c.fetchone()
        
        if result and result[0]:
            metadata = json.loads(result[0])
            image_path = metadata.get('path', '')
            
            if Path(image_path).exists():
                return Image.open(image_path)
        
        self.close()
        return None
    
    def search_cases(self, stage=None, location=None, min_confidence=0.0):
        """Search cases with filters"""
        conn = self.connect()
        
        query = "SELECT * FROM cases WHERE metadata LIKE '%kaggle%' AND confidence >= ?"
        params = [min_confidence]
        
        if stage:
            query += " AND stage = ?"
            params.append(stage)
        
        if location:
            query += " AND location = ?"
            params.append(location)
        
        query += " ORDER BY uploaded_at DESC"
        
        cases = pd.read_sql_query(query, conn, params=params)
        self.close()
        
        return cases

# Initialize dataset manager
dataset_manager = DatasetManager()