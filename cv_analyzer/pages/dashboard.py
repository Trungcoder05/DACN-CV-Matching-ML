"""
Trang Dashboard thống kê tổng quan
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from collections import Counter


def page_dashboard():
    """Trang Dashboard thống kê"""
    
    # Hero banner
    st.markdown("""
    <div class="hero-banner">
        <h1>📈 Dashboard Thống kê</h1>
        <p>Tổng quan về các CV đã phân tích</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Kiểm tra có dữ liệu không
    if not st.session_state.history:
        st.info("📊 Chưa có dữ liệu thống kê. Hãy phân tích một số CV để xem dashboard!")
        
        # Demo data
        st.markdown("### 🎯 Tính năng Dashboard bao gồm:")
        
        features = [
            "📊 Tổng số CV đã phân tích",
            "⭐ Điểm trung bình của các ứng viên",
            "📈 Phân bố điểm số (histogram)",
            "🎯 Top kỹ năng xuất hiện nhiều nhất",
            "💼 Tỷ lệ phân bố theo vị trí ứng tuyển",
            "📅 Xu hướng theo thời gian",
            "🏆 Top ứng viên xuất sắc nhất"
        ]
        
        col1, col2 = st.columns(2)
        
        for idx, feature in enumerate(features):
            if idx % 2 == 0:
                with col1:
                    st.markdown(f"- {feature}")
            else:
                with col2:
                    st.markdown(f"- {feature}")
        
        return
    
    # Tính toán metrics
    history = st.session_state.history
    total_cvs = len(history)
    avg_score = sum(item['score'] for item in history) / total_cvs if total_cvs > 0 else 0
    
    excellent_count = sum(1 for item in history if item['score'] >= 80)
    good_count = sum(1 for item in history if 65 <= item['score'] < 80)
    fair_count = sum(1 for item in history if 50 <= item['score'] < 65)
    poor_count = sum(1 for item in history if item['score'] < 50)
    
    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">📄</div>
            <div class="metric-value">{total_cvs}</div>
            <div class="metric-label">CV đã phân tích</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">⭐</div>
            <div class="metric-value">{avg_score:.1f}</div>
            <div class="metric-label">Điểm trung bình</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">🏆</div>
            <div class="metric-value">{excellent_count}</div>
            <div class="metric-label">Xuất sắc (≥80)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">✅</div>
            <div class="metric-value">{good_count}</div>
            <div class="metric-label">Phù hợp (65-79)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Biểu đồ phân bố
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Phân bố mức độ phù hợp")
        
        # Pie chart
        labels = ['Xuất sắc (≥80)', 'Phù hợp (65-79)', 'Cần cải thiện (50-64)', 'Chưa phù hợp (<50)']
        values = [excellent_count, good_count, fair_count, poor_count]
        colors = ['#38ef7d', '#667eea', '#ffa500', '#ff6b6b']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            showlegend=True,
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Be Vietnam Pro, sans-serif', 'size': 11}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Histogram phân bố điểm")
        
        scores = [item['score'] for item in history]
        
        fig = go.Figure(data=[go.Histogram(
            x=scores,
            nbinsx=20,
            marker=dict(
                color='#667eea',
                line=dict(color='white', width=1)
            )
        )])
        
        fig.update_layout(
            xaxis_title="Điểm số",
            yaxis_title="Số lượng",
            showlegend=False,
            height=350,
            margin=dict(t=20, b=40, l=40, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Be Vietnam Pro, sans-serif'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Thống kê theo vị trí
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 💼 Phân bố theo vị trí ứng tuyển")
    
    job_titles = [item['job_title'] for item in history]
    job_counter = Counter(job_titles)
    
    if job_counter:
        df_jobs = pd.DataFrame([
            {'Vị trí': job, 'Số lượng': count}
            for job, count in job_counter.most_common(10)
        ])
        
        fig = px.bar(
            df_jobs,
            x='Vị trí',
            y='Số lượng',
            color='Số lượng',
            color_continuous_scale='Blues',
            text='Số lượng'
        )
        
        fig.update_traces(textposition='outside')
        
        fig.update_layout(
            showlegend=False,
            height=350,
            margin=dict(t=20, b=100, l=40, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Be Vietnam Pro, sans-serif'}
        )
        
        fig.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top ứng viên
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🏆 Top 10 ứng viên xuất sắc nhất")
    
    # Sắp xếp theo điểm
    sorted_history = sorted(history, key=lambda x: x['score'], reverse=True)[:10]
    
    df_top = pd.DataFrame([
        {
            'Hạng': idx + 1,
            'Họ tên': item['name'],
            'Vị trí': item['job_title'],
            'Điểm': f"{item['score']:.1f}",
            'Mức độ': item['fit_level'],
            'Ngày phân tích': item['timestamp'].strftime('%d/%m/%Y %H:%M')
        }
        for idx, item in enumerate(sorted_history)
    ])
    
    # Style theo điểm
    def highlight_score(row):
        score = float(row['Điểm'])
        if score >= 90:
            return ['background-color: #e8f5e9'] * len(row)
        elif score >= 80:
            return ['background-color: #f1f8e9'] * len(row)
        else:
            return [''] * len(row)
    
    st.dataframe(
        df_top.style.apply(highlight_score, axis=1),
        use_container_width=True,
        height=400
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Xu hướng theo thời gian
    if len(history) > 1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📅 Xu hướng điểm theo thời gian")
        
        df_timeline = pd.DataFrame([
            {
                'Thời gian': item['timestamp'],
                'Điểm': item['score'],
                'Tên': item['name']
            }
            for item in sorted(history, key=lambda x: x['timestamp'])
        ])
        
        fig = px.line(
            df_timeline,
            x='Thời gian',
            y='Điểm',
            markers=True,
            hover_data=['Tên']
        )
        
        fig.add_hline(
            y=avg_score,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Trung bình: {avg_score:.1f}"
        )
        
        fig.update_traces(
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#764ba2')
        )
        
        fig.update_layout(
            xaxis_title="Thời gian",
            yaxis_title="Điểm",
            showlegend=False,
            height=350,
            margin=dict(t=20, b=40, l=40, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Be Vietnam Pro, sans-serif'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Xóa lịch sử
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True):
            st.session_state.history = []
            st.success("✅ Đã xóa lịch sử!")
            st.rerun()
