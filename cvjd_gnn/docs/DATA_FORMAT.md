# Quy cách dữ liệu CV–JD

CSV UTF-8 hoặc UTF-8 BOM, có hàng tiêu đề. Nếu nội dung chứa dấu phẩy, dấu nháy hoặc xuống dòng, dùng phần mềm xuất CSV đúng quy tắc. Mỗi thực thể chỉ có một ID ổn định. Dữ liệu nằm trong ba bảng liên kết bằng ID.

## `cvs.csv`

| Cột | Nội dung |
|---|---|
| `cv_id` | ID CV không rỗng, không lặp |
| `cv_text` | Văn bản CV không rỗng; không phải nhãn hay điểm số |
| `cv_skills` | Kỹ năng ngăn cách bằng `;`, ví dụ `Python; SQL; Git`; có thể rỗng |
| `source` | Nguồn hoặc mã nguồn để truy lại; thiếu nguồn sẽ được cảnh báo |

## `jobs.csv`

| Cột | Nội dung |
|---|---|
| `jd_id` | ID tin tuyển dụng không rỗng, không lặp |
| `jd_title` | Tên vị trí |
| `jd_text` | Mô tả và điều kiện tuyển dụng đầy đủ, không rỗng |
| `jd_skills` | Kỹ năng ngăn cách bằng `;`; có thể rỗng |
| `source` | URL nguồn hoặc mã tài liệu gốc |

Giữ bản gốc để phân biệt kỹ năng bắt buộc, ưu tiên và nhóm công nghệ lựa chọn. Bản đầu của đồ thị coi các cạnh kỹ năng cùng loại; chưa mã hóa AND/OR hoặc trọng số yêu cầu. Không dùng thông tin nhạy cảm như giới tính để gán nhãn phù hợp. Gỡ dữ liệu định danh không cần thiết khỏi văn bản trước khi đưa vào huấn luyện hoặc chia sẻ.

## `pairs.csv`

| Cột | Nội dung |
|---|---|
| `cv_id` | Tham chiếu CV có trong `cvs.csv` |
| `jd_id` | Tham chiếu JD có trong `jobs.csv` |
| `label` | `low`, `medium`, `high`; cũng nhận `0/1/2` hoặc `Thấp/Trung bình/Cao`; để trống nếu chưa gán |
| `label_source` | `human` nếu người đã đánh giá, `heuristic` nếu tự động theo quy tắc; demo riêng dùng `synthetic` |
| `split` | `train`, `validation`, `test`; hoặc để trống toàn bộ rồi chạy `prepare` |

Một cặp CV–JD chỉ có một dòng. Không tự gán nhãn “low” cho mọi cặp chưa quan sát. Bộ huấn luyện cần cả ba lớp; validation/test cần có nhãn để tính chỉ số. `validate` thông thường chấp nhận nhãn trống để phục vụ giai đoạn thu thập; `validate --for-training` kiểm tra điều kiện chạy mô hình.

Một CV phải nằm trong đúng một tập. Các CV khác ID nhưng giống nội dung sau chuẩn hóa chữ hoa/thường và khoảng trắng cũng không được chia sang nhiều tập. Code chưa phát hiện gần trùng theo ngữ nghĩa hay nhiều CV của cùng một người; nhóm cần rà soát thêm khi thu thập.

Khi `prepare` tự chia, tỷ lệ khoảng 70/15/15 tính trên nhóm nội dung CV, không phải số dòng cặp. Chưa phân tầng theo nhãn; kiểm tra `validate` sau khi chia để thấy phân bố từng lớp. Không thay seed nhiều lần chỉ để chọn kết quả test thuận lợi.

## Nguồn nhãn và đánh giá

`human` là thông tin do nhóm khai báo, không phải xác minh độc lập của chương trình. Cần lưu danh tính/mã người đánh giá, tiêu chí và cách giải quyết bất đồng trong tài liệu gán nhãn riêng. Không cho người gán nhãn nhìn thấy dự đoán mô hình hoặc nhãn quy tắc nếu muốn đánh giá độc lập.

Adapter CSV tổng hợp mặc định đọc `human_label`; nếu chưa có nhãn thì giữ trống. Muốn dùng `heuristic_label` phải truyền `--label-column heuristic_label --label-source heuristic` và thêm `--allow-weak-labels` khi huấn luyện. Có thể dùng nhãn yếu ở train và nhãn người ở validation/test; mỗi dòng cần khai báo đúng nguồn, metrics sẽ ghi phân bố nguồn nhãn theo tập.

Không đưa `skill_overlap_percent`, `heuristic_label`, `matched_skills` hoặc `human_label` vào đặc trưng văn bản/nút để dự đoán chính các nhãn đó. Adapter chỉ lấy văn bản và kỹ năng độc lập của từng CV/JD làm đầu vào mô hình.

## Manifest tùy chọn

Nếu có, `manifest.json` có thể chứa:

```json
{
  "dataset_kind": "research",
  "version": "v1",
  "notes": "Nguồn dữ liệu và tài liệu gán nhãn của nhóm"
}
```

Chỉ dùng `dataset_kind: synthetic_demo` cho dữ liệu giả lập kiểm thử. Số lượng trên 3.000 bản ghi không tự chứng minh đủ chất lượng hoặc đúng phạm vi thực tập; cần thống nhất cách đếm với giảng viên.
