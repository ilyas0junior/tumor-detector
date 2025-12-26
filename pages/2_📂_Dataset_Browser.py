# pages/2_📂_Dataset_Browser.py
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dataset_manager import dataset_manager
from utils.database import get_statistics

st.set_page_config(
    page_title="Dataset Browser",
    page_icon="📂",
    layout="wide"
)

# Title
st.title("📂 Brain Tumor MRI Dataset Browser")
st.markdown("Explore the real Kaggle brain tumor MRI dataset")

# Get dataset stats
with st.spinner("Loading dataset..."):
    try:
        dataset_stats = dataset_manager.get_dataset_stats()
        all_cases = dataset_manager.search_cases()
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        dataset_stats = {}
        all_cases = pd.DataFrame()

# Filters sidebar
with st.sidebar:
    st.subheader("🔍 Filters")
    
    # Stage filter
    stages = ["All Stages", "Stage I", "Stage II", "Stage III", "Stage IV", "No tumor"]
    selected_stage = st.selectbox("Tumor Stage", stages)
    
    # Confidence filter
    min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.1)
    
    # Malignancy filter
    malignancies = ["All", "Low", "Moderate", "High", "None"]
    selected_malignancy = st.selectbox("Malignancy Level", malignancies)
    
    # Items per page
    items_per_page = st.select_slider("Items per page", [12, 24, 48, 96], value=24)
    
    st.divider()
    
    # Dataset stats
    st.subheader("📊 Dataset Stats")
    if dataset_stats:
        col1, col2 = st.columns(2)
        col1.metric("Total", dataset_stats.get('total_cases', 0))
        col2.metric("Tumors", dataset_stats.get('tumor_cases', 0))
        
        if dataset_stats.get('stage_distribution'):
            st.caption("Stage Distribution:")
            for stage, count in dataset_stats['stage_distribution'].items():
                st.caption(f"  {stage}: {count}")

# Main content
if not all_cases.empty:
    # Apply filters
    filtered_cases = all_cases.copy()
    
    if selected_stage != "All Stages":
        filtered_cases = filtered_cases[filtered_cases['stage'] == selected_stage]
    
    if selected_malignancy != "All":
        filtered_cases = filtered_cases[filtered_cases['malignancy'] == selected_malignancy]
    
    filtered_cases = filtered_cases[filtered_cases['confidence'] >= min_confidence]
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Filtered Cases", len(filtered_cases))
    col2.metric("Showing", f"{min(items_per_page, len(filtered_cases))}")
    col3.metric("Pages", f"{max(1, (len(filtered_cases) + items_per_page - 1) // items_per_page)}")
    
    # Pagination
    if len(filtered_cases) > 0:
        total_pages = max(1, (len(filtered_cases) + items_per_page - 1) // items_per_page)
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        
        start_idx = (page_number - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_cases))
        
        page_cases = filtered_cases.iloc[start_idx:end_idx]
        
        st.divider()
        
        # Display cases in grid
        cols = st.columns(4)
        
        for idx, (_, case) in enumerate(page_cases.iterrows()):
            col_idx = idx % 4
            
            with cols[col_idx]:
                # Try to load image
                try:
                    case_image = dataset_manager.get_case_image(case['case_id'])
                    if case_image:
                        st.image(case_image, use_container_width=True)
                    else:
                        # Placeholder
                        st.image("https://via.placeholder.com/200x200/3949ab/ffffff?text=MRI", use_container_width=True)
                except:
                    st.image("https://via.placeholder.com/200x200/ccc/666?text=Image+Not+Found", use_container_width=True)
                
                # Case info
                stage_color = {
                    'Stage I': '#4CAF50',
                    'Stage II': '#8BC34A',
                    'Stage III': '#FFC107',
                    'Stage IV': '#F44336',
                    'No tumor': '#2196F3'
                }.get(case.get('stage', 'Unknown'), '#666')
                
                st.markdown(f"""
                <div style="padding: 10px; background: #f5f7ff; border-radius: 8px; margin-top: 5px;">
                    <p style="margin: 0; font-weight: bold; color: #1a237e;">{case['case_id'][:15]}</p>
                    <p style="margin: 5px 0;">
                        <span style="background: {stage_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">
                            {case.get('stage', 'Unknown')}
                        </span>
                    </p>
                    <p style="margin: 3px 0; font-size: 0.85rem; color: #555;">
                        📏 {case.get('tumor_size', 'N/A')}
                    </p>
                    <p style="margin: 3px 0; font-size: 0.85rem; color: #555;">
                        🎯 {float(case.get('confidence', 0)):.0%}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Pagination info
        st.caption(f"📄 Page {page_number} of {total_pages} • Showing {len(page_cases)} of {len(filtered_cases)} cases")
        
        # Export button
        if st.button("📥 Export Filtered Results (CSV)", type="secondary"):
            csv = filtered_cases.to_csv(index=False)
            st.download_button(
                label="⬇️ Click to Download",
                data=csv,
                file_name=f"brain_tumor_dataset_filtered.csv",
                mime="text/csv"
            )
    
    else:
        st.info("No cases match the selected filters.")
        
else:
    st.warning("Dataset not loaded. Please run setup_database.py first.")

# Visualizations
if not all_cases.empty:
    st.divider()
    st.subheader("📈 Dataset Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Stage distribution
        stage_counts = all_cases['stage'].value_counts()
        fig1 = px.bar(
            x=stage_counts.index,
            y=stage_counts.values,
            title="Cases by Stage",
            labels={'x': 'Stage', 'y': 'Count'},
            color=stage_counts.index,
            color_discrete_sequence=['#4CAF50', '#8BC34A', '#FFC107', '#F44336', '#2196F3']
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Confidence distribution
        fig2 = px.histogram(
            all_cases,
            x='confidence',
            nbins=20,
            title="Confidence Distribution",
            labels={'confidence': 'Confidence Level'},
            color_discrete_sequence=['#3949ab']
        )
        fig2.update_layout(xaxis=dict(tickformat=".0%"))
        st.plotly_chart(fig2, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>Brain Tumor MRI Dataset • Kaggle: masoudnickparvar/brain-tumor-mri-dataset</p>
</div>
""", unsafe_allow_html=True)