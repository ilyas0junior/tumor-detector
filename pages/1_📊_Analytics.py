# pages/1_📊_Analytics.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_all_cases, get_statistics
from utils.dataset_manager import dataset_manager

st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Analytics Dashboard")
st.markdown("Comprehensive analysis of all tumor detection cases")

# Get data
with st.spinner("Loading analytics..."):
    cases_df = get_all_cases()
    stats = get_statistics()

# KPI Cards
st.subheader("📈 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cases", stats.get('total_cases', 0))

with col2:
    if stats.get('stage_distribution'):
        most_common = max(stats['stage_distribution'].items(), key=lambda x: x[1])[0]
        st.metric("Most Common", most_common)
    else:
        st.metric("Most Common", "N/A")

with col3:
    st.metric("Avg Confidence", f"{stats.get('avg_confidence', 0):.1%}")

with col4:
    if not cases_df.empty:
        recent = pd.to_datetime(cases_df['uploaded_at']).max().strftime('%Y-%m-%d')
        st.metric("Last Analysis", recent)
    else:
        st.metric("Last Analysis", "Never")

st.divider()

# Charts
if not cases_df.empty and stats['total_cases'] > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        # Stage distribution
        stage_data = cases_df['stage'].value_counts().reset_index()
        stage_data.columns = ['Stage', 'Count']
        
        fig1 = px.pie(
            stage_data,
            values='Count',
            names='Stage',
            title="📊 Stage Distribution",
            hole=0.4,
            color='Stage',
            color_discrete_map={
                'Stage I': '#4CAF50',
                'Stage II': '#8BC34A',
                'Stage III': '#FFC107',
                'Stage IV': '#F44336',
                'No tumor': '#2196F3'
            }
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Confidence over time
        cases_df['date'] = pd.to_datetime(cases_df['uploaded_at']).dt.date
        
        daily_conf = cases_df.groupby('date')['confidence'].mean().reset_index()
        
        fig2 = px.line(
            daily_conf,
            x='date',
            y='confidence',
            title="📈 Average Confidence Over Time",
            markers=True,
            line_shape='spline'
        )
        fig2.update_layout(
            yaxis_title="Confidence",
            yaxis=dict(range=[0, 1], tickformat=".0%"),
            xaxis_title="Date"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Recent cases table
    st.subheader("📋 Recent Cases")
    
    display_df = cases_df.head(20).copy()
    if not display_df.empty:
        display_df['uploaded_at'] = pd.to_datetime(display_df['uploaded_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Color coding for stage
        def color_stage(val):
            colors = {
                'Stage I': 'background-color: #e8f5e9',
                'Stage II': 'background-color: #f1f8e9',
                'Stage III': 'background-color: #fffde7',
                'Stage IV': 'background-color: #ffebee',
                'No tumor': 'background-color: #e3f2fd'
            }
            return colors.get(val, '')
        
        styled_df = display_df[['case_id', 'stage', 'confidence', 'tumor_count', 'malignancy', 'location', 'uploaded_at']].style\
            .applymap(color_stage, subset=['stage'])\
            .format({'confidence': '{:.1%}'})
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Export button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Data (CSV)",
            data=csv,
            file_name=f"tumor_cases_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Dataset statistics
    st.divider()
    st.subheader("🧠 Dataset Statistics")
    
    try:
        dataset_stats = dataset_manager.get_dataset_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Images", dataset_stats.get('total_cases', 0))
        col2.metric("Tumor Images", dataset_stats.get('tumor_cases', 0))
        col3.metric("Healthy Images", dataset_stats.get('healthy_cases', 0))
        col4.metric("Avg Confidence", f"{dataset_stats.get('avg_confidence', 0):.1%}")
        
    except Exception as e:
        st.info("Dataset statistics not available")

else:
    st.info("📭 No cases in database yet. Upload some images to see analytics!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>Analytics Dashboard • Updated in real-time</p>
</div>
""", unsafe_allow_html=True)