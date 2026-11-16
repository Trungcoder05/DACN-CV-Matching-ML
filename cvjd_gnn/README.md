# CV–JD GNN — Đồ án chuyên ngành

Dự án Python phân tích mức phù hợp giữa CV và vị trí thực tập CNTT bằng **GNN GraphSAGE trên đồ thị nhiều loại nút**, triển khai trực tiếp bằng PyTorch. Code chạy trên CPU, tự huấn luyện mô hình, không gọi API AI. Có pipeline dữ liệu, mô hình đối chứng, lưu checkpoint, đánh giá và chấm CV mới.

**Trạng thái:** đã có code chạy được với dữ liệu mẫu để kiểm thử. Chưa có kết quả nghiên cứu trên dataset hoàn chỉnh. Dữ liệu mẫu chỉ là nhân vật và công việc giả lập, không dùng số đo của nó làm kết quả đồ án.

## Mở và chạy trên máy này

Mở PowerShell tại `D:\DACN-CNPM`. Môi trường `.venv` đã được tạo. Không bắt buộc kích hoạt môi trường:

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn --help
```

Một bộ demo và run thử đã được tạo tại `data/demo` và `runs/demo`. Xem dự đoán của run đó:

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn predict --run runs/demo --cv-json data/demo/sample_cv.json --top-k 3
```

Để chạy lại từ đầu, dùng thư mục mới; code không ghi đè dataset/run đã có:

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn make-demo --output data/demo_new --cvs 60
.\.venv\Scripts\python.exe -m cvjd_gnn validate --data data/demo_new --for-training
.\.venv\Scripts\python.exe -m cvjd_gnn train --data data/demo_new --output runs/demo_new --config configs/train.json
.\.venv\Scripts\python.exe -m cvjd_gnn evaluate --run runs/demo_new --data data/demo_new
.\.venv\Scripts\python.exe -m cvjd_gnn predict --run runs/demo_new --cv-json data/demo_new/sample_cv.json --output runs/demo_new/prediction.csv
```

## Khi có dữ liệu hoàn chỉnh

Có hai cách đưa dữ liệu vào.

**Cách 1 — Ba bảng CSV chuẩn.** Lấy tiêu đề cột từ `data/templates/`, điền dữ liệu và lưu thành:

```text
data/raw/final/
  cvs.csv
  jobs.csv
  pairs.csv
```

Quy cách cột và nhãn được mô tả trong [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md). Nếu chưa chia tập, để trống toàn bộ cột `split`; lệnh `prepare` sẽ chia khoảng 70/15/15 theo nhóm nội dung CV. Nếu đã chia, điền đầy đủ `train`, `validation`, `test`.

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn prepare --data data/raw/final --output data/processed/final
.\.venv\Scripts\python.exe -m cvjd_gnn validate --data data/processed/final --for-training
.\.venv\Scripts\python.exe -m cvjd_gnn train --data data/processed/final --output runs/final_v1 --config configs/train.json
.\.venv\Scripts\python.exe -m cvjd_gnn evaluate --run runs/final_v1 --data data/processed/final
```

**Cách 2 — CSV tổng hợp giống file của nhóm.** Adapter đọc các cột `cv_id`, `cv_text`, `cv_skills_extracted`, `jd_id`, `jd_description`, `jd_required_skills`, `human_label`; dùng thêm `data_split` và thông tin nguồn nếu có.

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn import-wide --input 'C:\duong-dan\dataset_hoan_chinh.csv' --output data/processed/final
.\.venv\Scripts\python.exe -m cvjd_gnn validate --data data/processed/final --for-training
.\.venv\Scripts\python.exe -m cvjd_gnn train --data data/processed/final --output runs/final_v1 --config configs/train.json
```

Mặc định chỉ lấy `human_label`; ô trống được giữ trống. Code không tự đổi nhãn heuristic thành nhãn người. Có thể thay `--label-column` nếu tên cột của nhóm khác.

Nếu cần **thử nghiệm riêng với nhãn yếu**, phải khai báo rõ ở cả bước nhập và huấn luyện:

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn import-wide --input 'C:\duong-dan\dataset.csv' --output data/processed/weak_v1 --label-column heuristic_label --label-source heuristic
.\.venv\Scripts\python.exe -m cvjd_gnn train --data data/processed/weak_v1 --output runs/weak_v1 --allow-weak-labels --config configs/train.json
```

Nhãn yếu được ghi rõ trong metrics và run manifest. Không dùng kết quả học nhãn quy tắc để khẳng định độ chính xác với đánh giá chuyên gia. Pipeline không tự nhân bản mẫu để đạt 3.000; cần thống nhất với giảng viên số lượng CV, JD hoặc cặp được yêu cầu và tính số hợp lệ sau làm sạch.

## Dự đoán cho CV mới

Tạo JSON UTF-8 như sau:

```json
{
  "cv_text": "Nội dung CV đầy đủ...",
  "cv_skills": ["Python", "SQL", "Git"]
}
```

```powershell
.\.venv\Scripts\python.exe -m cvjd_gnn predict --run runs/final_v1 --cv-json data/raw/cv_moi.json --top-k 5 --output runs/final_v1/prediction_001.csv
```

Cũng nhận file văn bản qua `--cv-text data/raw/cv_moi.txt`; khi không có danh sách kỹ năng, chương trình dùng từ điển kỹ năng đã biết để tìm từ khóa. Bản đầu chưa có OCR/PDF parser. Với PDF, trích văn bản và kiểm tra lại trước khi nhập.

Kết quả gồm vị trí, lớp dự đoán, điểm xếp hạng 0–100 và kỹ năng trùng/thiếu. Điểm bằng `100 × (0.5 × p_medium + p_high)`, không phải xác suất được tuyển. Danh sách kỹ năng trùng/thiếu là đối chiếu kỹ năng, không phải giải thích nhân quả của GNN.

## Mô hình và cách đánh giá

- Nút: CV, JD, kỹ năng. Cạnh: CV ↔ kỹ năng, JD ↔ kỹ năng. Không dùng nhãn phù hợp làm cạnh đầu vào.
- Đặc trưng văn bản: TF-IDF, chỉ fit trên CV train, danh mục JD đã biết và kỹ năng trong ngữ cảnh đó. Không fit trên CV validation/test. Chuẩn hóa một số tên như ReactJS → React, NodeJS → Node.js.
- Mô hình: chiếu đặc trưng → hai lớp GraphSAGE theo từng loại quan hệ → bộ phân loại cặp CV–JD ba lớp. Với mỗi quan hệ, lấy trung bình đặc trưng hàng xóm, biến đổi tuyến tính và cộng với biến đổi của nút đích. Các tham số ở `configs/train.json`. Dùng toàn bộ hàng xóm trong đồ thị, chưa có neighbor sampling.
- Giao thức: **CV mới, danh mục JD đã biết**. CV validation/test được thêm dưới dạng nút chỉ nhận thông tin từ kỹ năng, không gửi ngược vào đồ thị ngữ cảnh. Các CV truy vấn không ảnh hưởng lẫn nhau. Chưa đánh giá JD hoàn toàn mới.
- Huấn luyện: cross entropy có trọng số theo lớp của train, AdamW, dừng sớm và chọn checkpoint theo macro-F1 validation; dùng validation loss để phân xử khi hòa. Chỉ chấm test sau khi chọn checkpoint.
- Đối chứng: luôn đoán lớp phổ biến nhất của train; quy tắc trùng kỹ năng; TF-IDF cosine + logistic regression học trên train.
- Đánh giá: accuracy, macro-F1, precision/recall/F1 theo lớp, ma trận nhầm lẫn. Có xếp hạng khi suy luận; chưa báo cáo Recall@K/NDCG vì cần tập ứng viên có nhãn đủ để đánh giá xếp hạng.

TF-IDF là biểu diễn khởi đầu để pipeline gọn và chạy CPU. Từ vựng gồm unigram/bigram; `idf = log((1 + số tài liệu)/(1 + số tài liệu chứa từ)) + 1`, `tf = 1 + log(số lần xuất hiện)`, sau đó chuẩn hóa L2. Các phép tính này và logistic regression đối chứng dùng thư viện chuẩn/PyTorch. Không cần NumPy, SciPy, scikit-learn hay PyTorch Geometric cho bản triển khai này.

Dữ liệu khác ngôn ngữ hoặc nhiều cách diễn đạt có thể cần encoder đa ngôn ngữ sau này. Code không bảo đảm GNN tốt hơn mô hình đối chứng; cần đo bằng dữ liệu thật và tập nhãn độc lập.

## Kết quả của mỗi lần chạy

```text
runs/<ten-run>/
  model.pt               # trọng số checkpoint tốt nhất
  text_encoder.json      # từ vựng + IDF, phục hồi không fit lại
  graph_context.pt       # đồ thị ngữ cảnh của train + JD đã biết
  graph_metadata.json    # ánh xạ node
  job_catalog.json       # danh mục công việc để suy luận
  run.json               # config, phiên bản thư viện, nguồn nhãn, hash dữ liệu
  metrics.json           # GNN và các đối chứng
  history.csv            # loss và macro-F1 qua từng epoch
  test_predictions.csv   # dự đoán từng cặp test
```

`evaluate` kiểm tra hash để không vô tình đánh giá một checkpoint với dataset đã thay đổi. Dùng dataset thay đổi thì tạo run mới. Run vẫn chứa đặc trưng xuất phát từ dữ liệu; `data/raw`, `data/processed`, `.venv` và `runs` được loại khỏi Git mặc định.

## Cài lại trên máy khác

Cần `uv`. Đã cố định Python 3.12 và thư viện trong `uv.lock`; mặc định tải PyTorch CPU, không cần GPU:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Lệnh trên cài vào `.venv`, đặt Python tải về trong `.python` và cache trong `.cache`. Nếu dùng GPU, cần chủ động đổi bản PyTorch, tạo lại lock và kiểm thử môi trường trước khi đặt `device` thành `cuda`.

## Kiểm thử và cấu trúc code

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\ruff.exe check src tests
```

| File | Vai trò |
|---|---|
| `src/cvjd_gnn/data.py` | Schema, chuẩn hóa, chia tập, nhập CSV và kiểm tra |
| `src/cvjd_gnn/features.py` | TF-IDF và lưu/tải bộ mã hóa |
| `src/cvjd_gnn/graph.py` | Dựng đồ thị và gắn CV mới |
| `src/cvjd_gnn/model.py` | GNN GraphSAGE và phân loại cặp |
| `src/cvjd_gnn/training.py` | Huấn luyện, chọn checkpoint, ghi kết quả |
| `src/cvjd_gnn/metrics.py` | Chỉ số và các mô hình đối chứng |
| `src/cvjd_gnn/predict.py` | Dự đoán CV mới và đánh giá lại |
| `src/cvjd_gnn/cli.py` | Các lệnh sử dụng |
| `scripts/audit_dataset.py` | Script kiểm tra CSV tổng hợp ở bước trước |
| `reports/dataset_audit_vi.md` | Nhận xét bộ dữ liệu nhóm đã gửi |

Tham khảo thuật toán: [bài báo GraphSAGE — Hamilton, Ying, Leskovec](https://arxiv.org/abs/1706.02216). Phép tổng hợp hàng xóm dùng [PyTorch Tensor.index_add_](https://docs.pytorch.org/docs/stable/generated/torch.Tensor.index_add_.html).
