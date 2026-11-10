"""
Trang giới thiệu đồ án
"""

import streamlit as st


def page_about():
    """Trang giới thiệu"""
    
    # Hero banner
    st.markdown("""
    <div class="hero-banner">
        <h1>ℹ️ Giới thiệu Đồ án</h1>
        <p>Hệ thống phân tích CV và đánh giá mức độ phù hợp bằng Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Thông tin đồ án
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🎓 Thông tin Đồ án Tốt Nghiệp")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        **Tên đề tài:**
        
        **Sinh viên thực hiện:**
        
        **MSSV:**
        
        **Lớp:**
        
        **Khoa:**
        
        **Giảng viên hướng dẫn:**
        
        **Năm học:**
        """)
    
    with col2:
        st.markdown("""
        Phân tích CV và đánh giá mức độ phù hợp với vị trí thực tập CNTT bằng học máy
        
        [Tên sinh viên]
        
        [Mã số sinh viên]
        
        [Tên lớp]
        
        Công nghệ Thông tin
        
        [Tên giảng viên]
        
        2024-2025
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mục tiêu
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Mục tiêu Đồ án")
    
    st.markdown("""
    1. **Tự động hóa quy trình sàng lọc CV**: Giảm thời gian và công sức cho HR/Nhà tuyển dụng
    
    2. **Đánh giá khách quan**: Sử dụng ML để đánh giá mức độ phù hợp một cách công bằng
    
    3. **Hỗ trợ ứng viên**: Đưa ra gợi ý cải thiện CV cụ thể và lộ trình học tập
    
    4. **So sánh nhiều ứng viên**: Xếp hạng và so sánh để chọn ứng viên phù hợp nhất
    
    5. **Hỗ trợ tiếng Việt**: Xử lý CV tiếng Việt, tiếng Anh và song ngữ
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tính năng
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### ✨ Tính năng Chính")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📄 Phân tích CV đơn lẻ:**
        - Upload PDF/DOCX, OCR cho CV scan
        - Trích xuất: tên, email, SĐT, GPA, kỹ năng, kinh nghiệm, dự án
        - Chấm điểm 0-100 với 4 mức độ phù hợp
        - Radar chart, gauge chart trực quan
        - Gợi ý cải thiện cụ thể
        - Xuất báo cáo Excel/Text
        
        **📊 So sánh nhiều CV:**
        - Batch upload, xử lý đồng thời
        - Xếp hạng theo điểm
        - Lọc theo ngưỡng điểm
        - Biểu đồ phân bố
        - Xuất báo cáo tổng hợp Excel
        """)
    
    with col2:
        st.markdown("""
        **📈 Dashboard thống kê:**
        - Tổng số CV đã phân tích
        - Điểm trung bình, phân bố mức độ
        - Histogram điểm số
        - Top ứng viên xuất sắc
        - Xu hướng theo thời gian
        
        **🤖 Machine Learning:**
        - TF-IDF Vectorization (1000 features)
        - Multiple models: Ridge, Random Forest, XGBoost
        - R² Score: ~0.87, MAE: ~7.2
        - Kết hợp rule-based và ML (70-30)
        - Synthetic dataset: 1000 samples
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tech stack
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Công nghệ Sử dụng")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Backend & ML:**
        - Python 3.8+
        - scikit-learn
        - XGBoost
        - Pandas, NumPy
        """)
    
    with col2:
        st.markdown("""
        **NLP & Document:**
        - pdfplumber, PyMuPDF
        - python-docx
        - pytesseract (OCR)
        - underthesea (Tiếng Việt)
        """)
    
    with col3:
        st.markdown("""
        **Frontend:**
        - Streamlit
        - Plotly
        - streamlit-option-menu
        - Custom CSS
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Hướng phát triển
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Hướng Phát triển Tương lai")
    
    st.markdown("""
    1. **Tích hợp Deep Learning:**
       - BERT/PhoBERT cho NLP tiếng Việt tốt hơn
       - Named Entity Recognition (NER) nâng cao
    
    2. **Mở rộng dữ liệu:**
       - Thu thập CV thật từ các nguồn hợp pháp
       - Fine-tune model trên domain cụ thể
    
    3. **Tính năng mới:**
       - Matching CV với nhiều JD cùng lúc
       - Chatbot tư vấn CV
       - Video interview analysis (CV + phỏng vấn)
    
    4. **Deployment:**
       - Web app public (Streamlit Cloud/Heroku)
       - API RESTful cho tích hợp
       - Mobile app
    
    5. **Bảo mật:**
       - Encryption cho dữ liệu nhạy cảm
       - GDPR compliance
       - Authentication & Authorization
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Liên hệ
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 📞 Liên hệ")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📧 Email:**
        
        [your.email@example.com]
        """)
    
    with col2:
        st.markdown("""
        **🔗 GitHub:**
        
        [github.com/yourusername]
        """)
    
    with col3:
        st.markdown("""
        **💼 LinkedIn:**
        
        [linkedin.com/in/yourprofile]
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
