"""
Trang so sánh nhiều CV cùng lúc (Batch mode)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
import tempfile
import os

from core import CVExtractor, CVScorer, ReportGenerator, get_all_job_titles


def page_batch_comparison():
    """Trang so sánh nhiều CV"""
    
    # Hero banner
    st.markdown("""
    <div class="hero-banner">
        <h1>📊 So sánh nhiều CV cùng lúc</h1>
        <p>Upload nhiều CV để xếp hạng và so sánh ứng viên</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Components
    extractor = CVExtractor()
    model_path = Path("cv_analyzer/models/cv_scorer_model.pkl")
    scorer = CVScorer(model_path=str(model_path) if model_path.exists() else None)
    report_gen = ReportGenerator()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📤 Upload nhiều CV")
        
        uploaded_files = st.file_uploader(
            "Chọn nhiều file CV (PDF hoặc DOCX)",
            type=['pdf', 'docx', 'doc'],
            accept_multiple_files=True,
            help="Có thể chọn nhiều file cùng lúc"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 💼 Vị trí tuyển dụng")
        
        job_titles = get_all_job_titles()
        selected_job = st.selectbox(
            "Chọn vị trí",
            options=job_titles
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Job Description tùy chỉnh
    with st.expander("📝 Thêm mô tả công việc tùy chỉnh (tùy chọn)"):
        custom_jd = st.text_area(
            "Paste Job Description ở đây",
            height=120
        )
    
    # Nút phân tích
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        analyze_button = st.button(
            "🚀 Phân tích tất cả CV",
            use_container_width=True,
            type="primary"
        )
    
    # Xử lý batch analysis
    if analyze_button:
        if not uploaded_files:
            st.error("⚠️ Vui lòng upload ít nhất 1 file CV!")
            return
        
        st.markdown("---")
        st.markdown("## 🔄 Đang phân tích...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        cv_info_list = []
        
        # Trích xuất thông tin từ tất cả CV
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Đang xử lý {uploaded_file.name}...")
            
            try:
                # Lưu file tạm
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=Path(uploaded_file.name).suffix
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Trích xuất
                cv_info = extractor.extract_all_info(tmp_path)
                cv_info['filename'] = uploaded_file.name
                cv_info_list.append(cv_info)
                
                # Xóa file tạm
                os.unlink(tmp_path)
                
            except Exception as e:
                st.warning(f"⚠️ Không thể xử lý {uploaded_file.name}: {str(e)}")
            
            # Update progress
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        # Chấm điểm tất cả CV
        if cv_info_list:
            status_text.text("Đang chấm điểm các CV...")
            
            results = scorer.batch_score_cvs(
                cv_info_list,
                selected_job,
                custom_jd if custom_jd else None
            )
            
            # Lưu vào session state
            st.session_state.batch_results = results
            
            progress_bar.progress(1.0)
            status_text.text(f"✅ Hoàn thành! Đã phân tích {len(results)} CV")
        else:
            st.error("❌ Không có CV nào được xử lý thành công!")
            return
    
    # Hiển thị kết quả
    if st.session_state.batch_results:
        display_batch_results(st.session_state.batch_results, selected_job, report_gen)


def display_batch_results(results, job_title, report_gen):
    """Hiển thị kết quả so sánh batch"""
    
    st.markdown("---")
    st.markdown("## 🏆 KẾT QUẢ XẾP HẠNG")
    
    # Metrics tổng quan
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">👥</div>
            <div class="metric-value">{len(results)}</div>
            <div class="metric-label">Ứng viên</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_score = sum(r['final_score'] for r in results) / len(results)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">📊</div>
            <div class="metric-value">{avg_score:.1f}</div>
            <div class="metric-label">Điểm TB</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        top_candidates = sum(1 for r in results if r['final_score'] >= 80)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">⭐</div>
            <div class="metric-value">{top_candidates}</div>
            <div class="metric-label">Xuất sắc</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        good_candidates = sum(1 for r in results if 65 <= r['final_score'] < 80)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">✅</div>
            <div class="metric-value">{good_candidates}</div>
            <div class="metric-label">Phù hợp</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bảng xếp hạng và biểu đồ
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Bảng xếp hạng chi tiết")
        
        # Tạo DataFrame
        df_display = pd.DataFrame([
            {
                'Hạng': r['rank'],
                'Họ tên': r['cv_name'],
                'Điểm': f"{r['final_score']:.1f}",
                'Mức độ': r['fit_level'],
                'Kỹ năng khớp': r['skill_match']['total_matched'],
                'Kỹ năng thiếu': len(r['skill_match']['missing_required'])
            }
            for r in results
        ])
        
        # Style DataFrame
        def color_score(val):
            try:
                score = float(val)
                if score >= 80:
                    return 'background-color: #e8f5e9; color: #2e7d32;'
                elif score >= 65:
                    return 'background-color: #e3f2fd; color: #1565c0;'
                elif score >= 50:
                    return 'background-color: #fff3e0; color: #ef6c00;'
                else:
                    return 'background-color: #ffebee; color: #c62828;'
            except:
                return ''
        
        st.dataframe(
            df_display.style.map(color_score, subset=['Điểm']),
            use_container_width=True,
            height=400
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Biểu đồ điểm số")
        
        # Bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=[r['cv_name'] for r in results],
                y=[r['final_score'] for r in results],
                marker=dict(
                    color=[r['final_score'] for r in results],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Điểm")
                ),
                text=[f"{r['final_score']:.1f}" for r in results],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            xaxis_title="Ứng viên",
            yaxis_title="Điểm",
            yaxis=dict(range=[0, 110]),
            showlegend=False,
            height=400,
            margin=dict(t=20, b=100),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Be Vietnam Pro, sans-serif'}
        )
        
        fig.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Phân bố điểm
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Phân bố điểm số")
    
    fig = go.Figure()
    
    scores = [r['final_score'] for r in results]
    
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=10,
        marker=dict(
            color='#667eea',
            line=dict(color='white', width=2)
        ),
        name='Số ứng viên'
    ))
    
    fig.update_layout(
        xaxis_title="Điểm",
        yaxis_title="Số ứng viên",
        showlegend=False,
        height=300,
        margin=dict(t=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Be Vietnam Pro, sans-serif'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lọc ứng viên
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Lọc ứng viên theo ngưỡng điểm")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        min_score = st.slider(
            "Điểm tối thiểu",
            min_value=0,
            max_value=100,
            value=65,
            step=5
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        filtered_count = sum(1 for r in results if r['final_score'] >= min_score)
        st.metric("Ứng viên đạt yêu cầu", filtered_count)
    
    filtered_results = [r for r in results if r['final_score'] >= min_score]
    
    if filtered_results:
        st.markdown(f"**Danh sách {len(filtered_results)} ứng viên đạt ngưỡng {min_score} điểm:**")
        
        for r in filtered_results:
            with st.expander(f"🏅 #{r['rank']} - {r['cv_name']} - {r['final_score']:.1f} điểm"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Kỹ năng khớp:**")
                    for skill in r['skill_match']['matched_required'][:10]:
                        st.markdown(f"✅ {skill}")
                
                with col2:
                    st.markdown("**Kỹ năng cần bổ sung:**")
                    for skill in r['skill_match']['missing_required'][:5]:
                        st.markdown(f"❌ {skill}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Xuất báo cáo Excel
    st.markdown("### 📥 Xuất báo cáo tổng hợp")
    
    excel_buffer = report_gen.export_batch_to_excel(results, job_title)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.download_button(
            label="📊 Tải báo cáo Excel",
            data=excel_buffer,
            file_name=f"batch_cv_analysis_{job_title.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
