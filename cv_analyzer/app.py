"""
CV Analyzer - Hệ thống phân tích CV và đánh giá mức độ phù hợp bằng Machine Learning
Ứng dụng Streamlit với giao diện đẹp, hiện đại
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path
import tempfile
import os
from datetime import datetime
from streamlit_option_menu import option_menu

# Import core modules
from core import (
    CVExtractor,
    CVScorer,
    ReportGenerator,
    get_all_job_titles,
    get_job_info
)

# ================== CẤU HÌNH TRANG ==================
st.set_page_config(
    page_title="CV Analyzer - Phân tích CV bằng AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== LOAD CSS ==================
def load_css():
    """Load custom CSS"""
    css_file = Path(__file__).parent / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# ================== KHỞI TẠO SESSION STATE ==================
if 'cv_info' not in st.session_state:
    st.session_state.cv_info = None
if 'score_result' not in st.session_state:
    st.session_state.score_result = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None

# ================== KHỞI TẠO CÁC CLASS ==================
@st.cache_resource
def init_components():
    """Khởi tạo các components (cached)"""
    extractor = CVExtractor()
    
    # Thử load model
    model_path = Path(__file__).parent / "models" / "cv_scorer_model.pkl"
    if model_path.exists():
        scorer = CVScorer(model_path=str(model_path))
    else:
        scorer = CVScorer()
    
    report_gen = ReportGenerator()
    
    return extractor, scorer, report_gen

extractor, scorer, report_gen = init_components()

# ================== SIDEBAR NAVIGATION ==================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1 style='color: white; font-size: 1.8rem; margin: 0;'>📄 CV Analyzer</h1>
        <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem;'>Phân tích CV bằng AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=[
            "🏠 Phân tích CV",
            "📊 So sánh nhiều CV",
            "📈 Dashboard",
            "🤖 Thông tin mô hình",
            "ℹ️ Giới thiệu"
        ],
        icons=['house', 'file-earmark-bar-graph', 'bar-chart', 'cpu', 'info-circle'],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "icon": {"color": "#667eea", "font-size": "1.2rem"},
            "nav-link": {
                "font-size": "0.95rem",
                "text-align": "left",
                "margin": "0.2rem 0",
                "padding": "0.6rem 1rem",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white"
            },
        }
    )

# ================== HELPER FUNCTIONS ==================

def create_hero_banner(title: str, subtitle: str):
    """Tạo hero banner đẹp"""
    st.markdown(f"""
    <div class="hero-banner">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(label: str, value: str, icon: str = "📊"):
    """Tạo metric card"""
    return f"""
    <div class="metric-card">
        <div style="font-size: 2rem;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def create_skill_tag(skill: str, tag_type: str = "matched"):
    """Tạo skill tag"""
    return f'<span class="skill-tag skill-{tag_type}">{skill}</span>'

def create_gauge_chart(score: float, fit_level: str):
    """Tạo gauge chart cho điểm"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>{fit_level}</b>", 'font': {'size': 24, 'color': '#667eea'}},
        number={'font': {'size': 60, 'color': '#667eea'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "#667eea"},
            'bar': {'color': "#667eea"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e8ecf3",
            'steps': [
                {'range': [0, 50], 'color': '#ffebee'},
                {'range': [50, 65], 'color': '#fff3e0'},
                {'range': [65, 80], 'color': '#e3f2fd'},
                {'range': [80, 100], 'color': '#e8f5e9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Be Vietnam Pro, sans-serif'}
    )
    
    return fig

def create_radar_chart(radar_data: dict):
    """Tạo radar chart"""
    categories = list(radar_data.keys())
    values = list(radar_data.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='#667eea', width=2),
        name='Năng lực ứng viên'
    ))
    
    # Thêm đường chuẩn (80 điểm)
    fig.add_trace(go.Scatterpolar(
        r=[80] * len(categories),
        theta=categories,
        fill='toself',
        fillcolor='rgba(118, 75, 162, 0.1)',
        line=dict(color='#764ba2', width=2, dash='dash'),
        name='Yêu cầu vị trí'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showline=True,
                linewidth=2,
                gridcolor='#e8ecf3'
            ),
            angularaxis=dict(
                linewidth=2,
                gridcolor='#e8ecf3'
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=450,
        margin=dict(l=80, r=80, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Be Vietnam Pro, sans-serif', 'size': 12}
    )
    
    return fig

def save_to_history(cv_info: dict, score_result: dict):
    """Lưu vào lịch sử"""
    history_item = {
        'timestamp': datetime.now(),
        'name': cv_info.get('name', 'Unknown'),
        'job_title': score_result.get('job_info', {}).get('description', '')[:30],
        'score': score_result['final_score'],
        'fit_level': score_result['fit_level']
    }
    st.session_state.history.append(history_item)

# ================== TRANG 1: PHÂN TÍCH CV ==================

def page_analyze_cv():
    """Trang phân tích CV đơn lẻ"""
    
    create_hero_banner(
        "🎯 Phân tích CV & Đánh giá mức độ phù hợp",
        "Upload CV của bạn và nhận đánh giá chi tiết từ hệ thống AI"
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📤 Upload CV")
        
        uploaded_file = st.file_uploader(
            "Chọn file CV (PDF hoặc DOCX)",
            type=['pdf', 'docx', 'doc'],
            help="Hỗ trợ file PDF và DOCX, tối đa 10MB"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 💼 Vị trí ứng tuyển")
        
        job_titles = get_all_job_titles()
        selected_job = st.selectbox(
            "Chọn vị trí",
            options=job_titles,
            help="Chọn vị trí bạn muốn ứng tuyển"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tùy chọn thêm Job Description
    with st.expander("📝 Thêm mô tả công việc tùy chỉnh (tùy chọn)"):
        custom_jd = st.text_area(
            "Paste Job Description ở đây",
            height=150,
            placeholder="Ví dụ: Chúng tôi tìm kiếm Backend Developer có kinh nghiệm với Python, Django..."
        )
    
    # Nút phân tích
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        analyze_button = st.button("🚀 Phân tích CV", use_container_width=True, type="primary")
    
    # Xử lý phân tích
    if analyze_button:
        if not uploaded_file:
            st.error("⚠️ Vui lòng upload file CV!")
            return
        
        with st.spinner("🔄 Đang phân tích CV... Vui lòng đợi trong giây lát..."):
            try:
                # Lưu file tạm
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Trích xuất thông tin
                cv_info = extractor.extract_all_info(tmp_path)
                
                # Chấm điểm
                score_result = scorer.score_cv(
                    cv_info,
                    selected_job,
                    custom_jd if custom_jd else None
                )
                
                # Lưu vào session state
                st.session_state.cv_info = cv_info
                st.session_state.score_result = score_result
                
                # Lưu lịch sử
                save_to_history(cv_info, score_result)
                
                # Xóa file tạm
                os.unlink(tmp_path)
                
                st.success("✅ Phân tích hoàn tất!")
                
            except Exception as e:
                st.error(f"❌ Lỗi khi phân tích CV: {str(e)}")
                return
    
    # Hiển thị kết quả
    if st.session_state.score_result:
        display_results()

def display_results():
    """Hiển thị kết quả phân tích"""
    cv_info = st.session_state.cv_info
    result = st.session_state.score_result
    
    st.markdown("---")
    st.markdown("## 📊 KẾT QUẢ PHÂN TÍCH")
    
    # Phần 1: Thông tin ứng viên và điểm tổng thể
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 👤 Thông tin ứng viên")
        st.markdown(f"**Họ tên:** {cv_info.get('name', 'N/A')}")
        st.markdown(f"**Email:** {cv_info.get('email', 'N/A')}")
        st.markdown(f"**Số điện thoại:** {cv_info.get('phone', 'N/A')}")
        st.markdown(f"**GPA:** {cv_info.get('gpa', 'N/A')}")
        st.markdown(f"**Số kỹ năng:** {len(cv_info.get('skills', []))}")
        st.markdown(f"**Số dự án:** {len(cv_info.get('projects', []))}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="score-container fade-in">', unsafe_allow_html=True)
        fig = create_gauge_chart(result['final_score'], result['fit_level'])
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<p style='text-align: center; color: #666;'>Phương pháp: {result['score_method']}</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Phần 2: Metrics
    st.markdown("### 📈 Chi tiết điểm số")
    
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("Kỹ năng kỹ thuật", result['breakdown']['skill_score'], "🔧", "/40"),
        ("Độ phù hợp văn bản", result['breakdown']['text_similarity_score'], "📝", "/25"),
        ("Kinh nghiệm/Dự án", result['breakdown']['experience_score'], "💼", "/20"),
        ("Học vấn", result['breakdown']['education_score'], "🎓", "/15")
    ]
    
    for col, (label, value, icon, max_score) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(
                create_metric_card(label, f"{value:.1f}{max_score}", icon),
                unsafe_allow_html=True
            )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Phần 3: Radar Chart và Skills
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Biểu đồ năng lực")
        fig = create_radar_chart(result['radar_data'])
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### ✅ Kỹ năng khớp")
        
        matched_req = result['skill_match']['matched_required']
        matched_pref = result['skill_match']['matched_preferred']
        
        if matched_req:
            st.markdown("**Kỹ năng bắt buộc:**")
            skills_html = "".join([create_skill_tag(s, "matched") for s in matched_req])
            st.markdown(f'<div>{skills_html}</div>', unsafe_allow_html=True)
        
        if matched_pref:
            st.markdown("<br>**Kỹ năng ưu tiên:**", unsafe_allow_html=True)
            skills_html = "".join([create_skill_tag(s, "matched") for s in matched_pref])
            st.markdown(f'<div>{skills_html}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Phần 4: Kỹ năng thiếu
    missing_skills = result['skill_match']['missing_required']
    if missing_skills:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### ❌ Kỹ năng cần bổ sung")
        skills_html = "".join([create_skill_tag(s, "missing") for s in missing_skills[:15]])
        st.markdown(f'<div>{skills_html}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Phần 5: Gợi ý cải thiện
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 💡 Gợi ý cải thiện")
    
    for suggestion in result['suggestions']:
        st.markdown(f"- {suggestion}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Phần 6: Xuất báo cáo
    st.markdown("### 📥 Tải báo cáo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Báo cáo Excel
        excel_buffer = report_gen.export_to_csv(cv_info, result)
        st.download_button(
            label="📊 Tải báo cáo Excel",
            data=excel_buffer,
            file_name=f"cv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # Báo cáo Text
        text_report = report_gen.generate_text_report(cv_info, result)
        st.download_button(
            label="📄 Tải báo cáo Text",
            data=text_report,
            file_name=f"cv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

# ================== MAIN ROUTER ==================

if selected == "🏠 Phân tích CV":
    page_analyze_cv()

elif selected == "📊 So sánh nhiều CV":
    from pages.batch_comparison import page_batch_comparison
    page_batch_comparison()

elif selected == "📈 Dashboard":
    from pages.dashboard import page_dashboard
    page_dashboard()

elif selected == "🤖 Thông tin mô hình":
    from pages.model_info import page_model_info
    page_model_info()

elif selected == "ℹ️ Giới thiệu":
    from pages.about import page_about
    page_about()
