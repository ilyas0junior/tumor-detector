# tumor_app.py - COMPLETE VERSION
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import plotly.graph_objects as go
import os
import sys
from datetime import datetime

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from utils.database import init_database, save_case, get_statistics
from utils.image_processor import analyze_tumor, create_visualization
from utils.dataset_manager import dataset_manager

# ===================== CONFIGURATION =====================
st.set_page_config(
    page_title="Brain Tumor Detector",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on app start
@st.cache_resource
def initialize_app():
    """Initialize app components"""
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database warning: {e}")
    return True

# Run initialization
initialize_app()

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    /* Main theme */
    .main {
        background: linear-gradient(135deg, #1a237e 0%, #311b92 100%);
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 20px;
    }
    
    .title {
        color: white;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .subtitle {
        color: #bbdefb;
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 40px;
    }
    
    /* Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.3);
        margin-bottom: 30px;
    }
    
    /* Upload area */
    .upload-zone {
        border: 3px dashed #3949ab;
        border-radius: 20px;
        padding: 60px 40px;
        text-align: center;
        background: rgba(245, 245, 255, 0.9);
        cursor: pointer;
        transition: all 0.3s;
        margin: 30px 0;
    }
    
    .upload-zone:hover {
        background: rgba(232, 234, 255, 0.95);
        border-color: #283593;
        transform: translateY(-2px);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #3949ab, #283593);
        color: white;
        border: none;
        padding: 15px 40px;
        border-radius: 50px;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.3s;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(57, 73, 171, 0.4);
    }
    
    /* Case cards */
    .case-card {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border-left: 5px solid #3949ab;
        transition: all 0.3s;
    }
    
    .case-card:hover {
        transform: translateX(5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.08);
        border-top: 5px solid #3949ab;
    }
</style>
""", unsafe_allow_html=True)

# ===================== SAMPLE DATA (Fallback) =====================
SAMPLE_CASES = pd.DataFrame({
    'case_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
    'stage': ['Stage I', 'Stage II', 'Stage III', 'Stage IV', 'Stage II'],
    'confidence': [0.92, 0.87, 0.78, 0.65, 0.88],
    'location': ['Brain', 'Brain', 'Brain', 'Brain', 'Brain'],
    'malignancy': ['Low', 'Moderate', 'High', 'High', 'Moderate'],
    'tumor_size': ['1.5 cm', '2.8 cm', '4.2 cm', '5.5 cm', '2.1 cm']
})

# ===================== HELPER FUNCTIONS =====================
def create_stage_gauge(stage, confidence):
    """Create beautiful gauge chart for stage"""
    colors = {
        'Stage I': '#4CAF50',
        'Stage II': '#8BC34A',
        'Stage III': '#FFC107',
        'Stage IV': '#F44336',
        'No tumor': '#2196F3'
    }
    
    color = colors.get(stage, '#9E9E9E')
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence * 100,
        number={'suffix': "%", 'font': {'size': 40, 'color': color}},
        title={'text': f"<b>{stage}</b>", 'font': {'size': 28, 'color': color}},
        delta={'reference': 70, 'increasing': {'color': color}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#f5f5f5'},
                {'range': [50, 75], 'color': '#eeeeee'},
                {'range': [75, 100], 'color': '#e0e0e0'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': confidence * 100
            }
        }
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

def display_similar_case(case):
    """Display a similar case card"""
    stage_color = {
        'Stage I': '#4CAF50',
        'Stage II': '#8BC34A',
        'Stage III': '#FFC107',
        'Stage IV': '#F44336',
        'No tumor': '#2196F3'
    }
    
    confidence_pct = f"{case.get('confidence', 0) * 100:.0f}%" if isinstance(case.get('confidence'), (int, float)) else "N/A"
    
    st.markdown(f"""
    <div class="case-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div>
                <h4 style="margin: 0; color: #1a237e;">📁 Case {case.get('case_id', 'Unknown')}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 0.9rem;">Brain MRI • {case.get('tumor_size', 'Size unknown')}</p>
            </div>
            <span style="
                background: {stage_color.get(case.get('stage', 'Unknown'), '#666')};
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-weight: bold;
                font-size: 0.9rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                {case.get('stage', 'Unknown')} • {confidence_pct}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
            <div>
                <p style="margin: 8px 0; color: #444;">
                    <b style="color: #3949ab;">📍 Location:</b><br>
                    {case.get('location', 'Brain')}
                </p>
                <p style="margin: 8px 0; color: #444;">
                    <b style="color: #3949ab;">⚠️ Malignancy:</b><br>
                    {case.get('malignancy', 'Unknown')}
                </p>
            </div>
            <div>
                <p style="margin: 8px 0; color: #444;">
                    <b style="color: #3949ab;">📏 Size:</b><br>
                    {case.get('tumor_size', 'Unknown')}
                </p>
                <p style="margin: 8px 0; color: #444;">
                    <b style="color: #3949ab;">🎯 Confidence:</b><br>
                    {confidence_pct}
                </p>
            </div>
        </div>
        
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px dashed #ccc;">
            <p style="margin: 0; color: #666; font-size: 0.85rem;">
                <b>Source:</b> {case.get('source', 'Kaggle Brain Tumor Dataset')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===================== SIDEBAR =====================
def render_sidebar():
    """Render the sidebar navigation"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #1a237e; margin: 0;">🧠</h1>
            <h3 style="color: #1a237e; margin: 10px 0;">Brain Tumor AI</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        st.page_link("tumor_app.py", label="🏠 Home", icon="🏠")
        st.page_link("pages/1_📊_Analytics.py", label="📊 Analytics", icon="📊")
        st.page_link("pages/2_📂_Dataset_Browser.py", label="📂 Dataset Browser", icon="📂")
        
        st.divider()
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        try:
            stats = get_statistics()
            col1, col2 = st.columns(2)
            col1.metric("Total", stats['total_cases'])
            col2.metric("Avg Conf", f"{stats['avg_confidence']:.0%}")
        except:
            col1, col2 = st.columns(2)
            col1.metric("Total", "0")
            col2.metric("Avg Conf", "0%")
        
        st.divider()
        
        # Sample images section
        st.subheader("🧪 Quick Test")
        if os.path.exists("sample_images"):
            sample_files = [f for f in os.listdir("sample_images") if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if sample_files:
                selected = st.selectbox("Try sample:", ["Select..."] + sample_files)
                if selected != "Select...":
                    if st.button("Use This Sample", type="secondary"):
                        st.session_state.sample_image = f"sample_images/{selected}"
                        st.rerun()
        
        st.divider()
        
        # App info
        st.markdown("""
        <div style="color: #666; font-size: 0.8rem; padding: 10px;">
            <p><b>Brain Tumor Detector v2.0</b></p>
            <p>AI-powered tumor stage analysis</p>
            <p>📍 Using real Kaggle MRI dataset</p>
        </div>
        """, unsafe_allow_html=True)

# ===================== MAIN APP =====================
def main():
    # Render sidebar
    render_sidebar()
    
    # Main header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="title">🧠 BRAIN TUMOR DETECTOR</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">AI-powered tumor stage analysis with real MRI dataset matching</p>', unsafe_allow_html=True)
    
    # Main content in glass card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader(
            "",
            type=['png', 'jpg', 'jpeg'],
            help="Upload brain MRI scan",
            label_visibility="collapsed"
        )
        
        if uploaded_file is None:
            st.markdown("""
            <div style="text-align: center;">
                <div style="font-size: 4rem; margin-bottom: 20px; color: #3949ab;">📁</div>
                <h3 style="color: #1a237e; margin-bottom: 10px;">Upload Brain MRI Scan</h3>
                <p style="color: #666;">Drag & drop or click to browse</p>
                <p style="color: #888; font-size: 0.9rem; margin-top: 20px;">
                    Supported: PNG, JPG, JPEG<br>
                    Recommended: Brain MRI scans
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # If image uploaded
    if uploaded_file is not None:
        # Display image and controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📷 Uploaded Image")
            image = Image.open(uploaded_file)
            st.image(image, caption="Original MRI Scan", use_column_width=True)
            
            # Image info
            img_info = f"Format: {uploaded_file.type.split('/')[-1].upper()} | Size: {uploaded_file.size / 1024:.0f} KB"
            st.caption(f"📊 {img_info}")
        
        with col2:
            st.subheader("⚡ Analysis Controls")
            
            # Analysis options
            with st.expander("⚙️ Settings", expanded=True):
                show_visualization = st.checkbox("Show tumor visualization", True)
                find_similar = st.checkbox("Find similar cases", True)
                save_to_db = st.checkbox("Save to database", True)
            
            # Analyze button
            if st.button("🔬 ANALYZE TUMOR", type="primary", use_container_width=True):
                with st.spinner("🧠 AI analyzing MRI scan..."):
                    # Progress simulation
                    progress_bar = st.progress(0)
                    for percent in range(0, 101, 20):
                        progress_bar.progress(percent / 100)
                        import time
                        time.sleep(0.1)
                    
                    # Analyze tumor
                    result = analyze_tumor(image)
                    
                    # Save to database
                    if save_to_db:
                        case_id = save_case(result)
                        if case_id:
                            st.success(f"✅ Case saved: **{case_id}**")
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("📊 Analysis Results")
                    
                    # Create gauge
                    gauge = create_stage_gauge(result['stage'], result['confidence'])
                    st.plotly_chart(gauge, use_container_width=True)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Stage", result['stage'])
                    col2.metric("Confidence", f"{result['confidence']:.1%}")
                    col3.metric("Tumors Found", result['tumor_count'])
                    col4.metric("Malignancy", result['malignancy'])
                    
                    # Visualization
                    if show_visualization and result['tumor_count'] > 0:
                        st.subheader("👁️ Tumor Visualization")
                        visualization = create_visualization(image)
                        st.image(visualization, caption="Green: Tumor boundaries | Red: Detection boxes", use_container_width=True)
                    
                    # Similar cases
                    if find_similar and result['stage'] != 'No tumor':
                        st.subheader("🔍 Similar Cases from Database")
                        
                        try:
                            # Get similar cases
                            similar_cases = dataset_manager.get_similar_real_cases(
                                stage=result['stage'],
                                location="Brain",
                                limit=3
                            )
                            
                            if not similar_cases.empty:
                                st.caption(f"Found {len(similar_cases)} similar {result['stage']} brain tumor cases")
                                
                                for _, case in similar_cases.iterrows():
                                    display_similar_case(case)
                            else:
                                # Fallback to samples
                                st.info("No similar cases found. Showing sample cases:")
                                for _, case in SAMPLE_CASES.iterrows():
                                    display_similar_case(case)
                                    
                        except Exception as e:
                            st.warning(f"Could not load similar cases: {e}")
                            st.info("Showing sample cases instead:")
                            for _, case in SAMPLE_CASES.iterrows():
                                display_similar_case(case)
        
        # Disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fff3cd, #ffeaa7); padding: 20px; border-radius: 15px; border-left: 5px solid #ffc107;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 1.8rem; margin-right: 15px;">⚠️</span>
                <h4 style="margin: 0; color: #856404;">IMPORTANT MEDICAL DISCLAIMER</h4>
            </div>
            <p style="margin: 0; color: #856404; font-size: 0.95rem;">
                This application is for <b>educational and research purposes only</b>. It is <b>NOT a medical device</b> 
                and should <b>NOT be used for diagnosis or treatment decisions</b>. Always consult with qualified 
                healthcare professionals for medical advice. Results may not be accurate.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close glass card
    
    # Footer
    st.markdown("""
    <div style="text-align: center; color: #5c6bc0; padding: 40px 20px;">
        <p style="margin: 5px 0; font-size: 1.1rem;">
            <b>Brain Tumor Detection AI</b> • Powered by Real MRI Dataset
        </p>
        <p style="margin: 5px 0; color: #7986cb; font-size: 0.9rem;">
            For research and educational purposes • Not for medical use
        </p>
        <p style="margin: 5px 0; color: #9fa8da; font-size: 0.8rem;">
            Made with Streamlit • Using OpenCV & Machine Learning
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()