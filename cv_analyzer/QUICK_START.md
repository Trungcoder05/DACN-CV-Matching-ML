# 🚀 Quick Start Guide - CV Analyzer

## 1️⃣ Cài đặt (5 phút)

```bash
# Bước 1: Di chuyển vào thư mục
cd cv_analyzer

# Bước 2: Cài đặt dependencies
pip install -r requirements.txt

# Bước 3: Huấn luyện model (tùy chọn, 2-3 phút)
python train_model.py

# Bước 4: Chạy app
streamlit run app.py
```

Truy cập: **http://localhost:8501**

## 2️⃣ Sử dụng cơ bản

### 📄 Phân tích 1 CV:
1. Chọn menu **"🏠 Phân tích CV"**
2. Upload file CV (PDF/DOCX)
3. Chọn vị trí ứng tuyển
4. Click **"🚀 Phân tích CV"**
5. Xem kết quả và tải báo cáo

### 📊 So sánh nhiều CV:
1. Chọn menu **"📊 So sánh nhiều CV"**
2. Upload nhiều file CV
3. Chọn vị trí
4. Click **"🚀 Phân tích tất cả CV"**
5. Xem bảng xếp hạng và xuất Excel

### 📈 Xem Dashboard:
1. Chọn menu **"📈 Dashboard"**
2. Xem thống kê tổng quan
3. Phân tích xu hướng

## 3️⃣ Cấu trúc File quan trọng

```
cv_analyzer/
├── app.py              ⭐ FILE CHẠY CHÍNH
├── train_model.py      🤖 Huấn luyện ML model
├── requirements.txt    📦 Dependencies
├── README.md           📖 Hướng dẫn đầy đủ
│
├── core/               💡 Logic xử lý
│   ├── extractor.py    → Trích xuất CV
│   ├── scorer.py       → Chấm điểm ML
│   ├── skills_db.py    → 150+ kỹ năng IT
│   └── ...
│
├── pages/              🎨 Giao diện
│   ├── batch_comparison.py
│   ├── dashboard.py
│   └── ...
│
├── models/             🧠 ML models đã train
│   └── cv_scorer_model.pkl
│
├── data/               💾 Dataset
│   └── synthetic_cv_dataset.csv
│
└── assets/             🎨 CSS, styles
    └── style.css
```

## 4️⃣ Tính năng chính

| Tính năng | Mô tả | Icon |
|-----------|-------|------|
| **Phân tích CV** | Upload & phân tích 1 CV | 🏠 |
| **So sánh Batch** | Xếp hạng nhiều CV | 📊 |
| **Dashboard** | Thống kê tổng quan | 📈 |
| **Model Info** | Chi tiết ML model | 🤖 |
| **Giới thiệu** | Thông tin đồ án | ℹ️ |

## 5️⃣ 10 Vị trí IT được hỗ trợ

1. 🔧 Backend Developer
2. 🎨 Frontend Developer
3. 🚀 Fullstack Developer
4. 📱 Mobile Developer
5. 📊 Data Analyst / Data Engineer
6. 🤖 AI / Machine Learning Engineer
7. ☁️ DevOps Engineer
8. 🧪 QA / Software Tester
9. 🎭 UI/UX Designer
10. 🔒 Cybersecurity / An toàn thông tin

## 6️⃣ ML Model Performance

```
✅ Best Model: Gradient Boosting
✅ R² Score: 0.9423
✅ MAE: 5.56 điểm
✅ Dataset: 1000 CVs synthetic
✅ Features: 1000 (TF-IDF)
```

## 7️⃣ Troubleshooting

### ❌ Lỗi: Module not found
```bash
pip install -r requirements.txt
```

### ❌ Lỗi OCR (CV scan không đọc được)
**Windows:**
1. Tải Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt và thêm vào PATH

**Mac:**
```bash
brew install tesseract tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-vie
```

### ❌ App không chạy được
```bash
# Kiểm tra Python version (cần 3.8+)
python --version

# Cài lại dependencies
pip install --upgrade -r requirements.txt

# Chạy với verbose mode
streamlit run app.py --logger.level=debug
```

### ❌ Model chưa được train
Không sao! App vẫn chạy được với **Rule-based method** (TF-IDF + Cosine Similarity).

Để train model:
```bash
python train_model.py
```

## 8️⃣ Tips & Tricks

### 💡 Để kết quả tốt hơn:
- ✅ Dùng CV có cấu trúc rõ ràng
- ✅ CV nên có: tên, email, kỹ năng, kinh nghiệm
- ✅ Font chữ chuẩn, không dùng ảnh thay chữ
- ✅ File PDF tốt hơn DOCX (đọc nhanh hơn)

### 🎯 Cải thiện điểm CV:
1. Thêm kỹ năng **bắt buộc** còn thiếu
2. Viết rõ dự án đã làm
3. Thêm GPA nếu >= 3.0/4.0
4. Có chứng chỉ ngoại ngữ (TOEIC, IELTS)
5. Highlight kinh nghiệm liên quan

### 🔧 Custom cho project của bạn:
**Thay đổi vị trí IT:**
- File: `core/skills_db.py`
- Thêm/sửa trong dict `JOB_DESCRIPTIONS`

**Thêm kỹ năng mới:**
- File: `core/skills_db.py`
- Thêm vào dict `SKILLS_DATABASE`

**Thay màu theme:**
- File: `assets/style.css`
- Sửa gradient colors

## 9️⃣ Export & Deploy

### 📥 Export code để nộp:
```bash
# Zip toàn bộ project
zip -r cv_analyzer.zip cv_analyzer/

# Hoặc chỉ lấy code (không có data/models)
zip -r cv_analyzer_code.zip cv_analyzer/ -x "cv_analyzer/data/*" "cv_analyzer/models/*"
```

### ☁️ Deploy lên Cloud:

**Streamlit Cloud (Free):**
1. Push code lên GitHub
2. Vào streamlit.io/cloud
3. Connect repository
4. Deploy!

**Heroku:**
```bash
heroku create cv-analyzer-app
git push heroku main
```

## 🔟 Câu hỏi thường gặp (FAQ)

**Q: App có cần internet không?**
A: Không! Chạy hoàn toàn offline trên máy local.

**Q: Có giới hạn số CV không?**
A: Không giới hạn. Batch mode có thể xử lý hàng trăm CV.

**Q: Dữ liệu CV có bị lưu lại không?**
A: Không! Chỉ lưu trong session, tắt app là mất.

**Q: Có thể thêm tiếng nước khác không?**
A: Có! Sửa file `preprocess.py` để thêm stopwords và NLP rules.

**Q: Accuracy của model là bao nhiêu?**
A: R² = 0.94, MAE = 5.56 điểm trên synthetic data.

**Q: Có thể dùng cho công ty thật không?**
A: Có! Nhưng nên train lại model với CV thật của công ty để tăng độ chính xác.

---

## 📞 Cần hỗ trợ?

- 📖 Đọc [README.md](README.md) đầy đủ
- 🐛 Báo lỗi: [GitHub Issues]
- 💬 Liên hệ: [email@example.com]

---

<div align="center">

**🎓 Good luck với đồ án!**

💡 Được xây dựng với ❤️ bằng Python & Streamlit

</div>
