"""
Module xuất báo cáo kết quả phân tích CV
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List
from io import BytesIO


class ReportGenerator:
    """Class tạo báo cáo"""
    
    def __init__(self):
        pass
    
    def generate_dataframe(self, cv_info: Dict, score_result: Dict) -> pd.DataFrame:
        """
        Tạo DataFrame từ kết quả phân tích
        
        Args:
            cv_info: thông tin CV
            score_result: kết quả chấm điểm
            
        Returns:
            df: DataFrame
        """
        data = {
            'Thông tin': [
                'Họ tên',
                'Email',
                'Số điện thoại',
                'GPA',
                'Vị trí ứng tuyển',
                'Điểm tổng thể',
                'Mức độ phù hợp',
                'Số kỹ năng khớp',
                'Kỹ năng bắt buộc khớp',
                'Số dự án',
                'Kinh nghiệm'
            ],
            'Giá trị': [
                cv_info.get('name', 'N/A'),
                cv_info.get('email', 'N/A'),
                cv_info.get('phone', 'N/A'),
                cv_info.get('gpa', 'N/A'),
                score_result.get('job_info', {}).get('description', 'N/A')[:50] + '...',
                f"{score_result['final_score']}/100",
                score_result['fit_level'],
                f"{score_result['skill_match']['total_matched']}",
                f"{len(score_result['skill_match']['matched_required'])}/{score_result['skill_match']['total_required']}",
                len(cv_info.get('projects', [])),
                len(cv_info.get('experience', []))
            ]
        }
        
        df = pd.DataFrame(data)
        return df
    
    def generate_skills_dataframe(self, score_result: Dict) -> pd.DataFrame:
        """
        Tạo DataFrame cho kỹ năng
        
        Args:
            score_result: kết quả chấm điểm
            
        Returns:
            df: DataFrame kỹ năng
        """
        skill_match = score_result['skill_match']
        
        data = {
            'Kỹ năng bắt buộc khớp': skill_match['matched_required'],
            'Kỹ năng ưu tiên khớp': skill_match['matched_preferred'],
            'Kỹ năng còn thiếu': skill_match['missing_required'][:10]
        }
        
        # Cân bằng độ dài
        max_len = max(len(v) for v in data.values())
        for key in data:
            while len(data[key]) < max_len:
                data[key].append('-')
        
        df = pd.DataFrame(data)
        return df
    
    def export_to_csv(
        self,
        cv_info: Dict,
        score_result: Dict,
        filename: str = None
    ) -> BytesIO:
        """
        Xuất báo cáo CSV
        
        Args:
            cv_info: thông tin CV
            score_result: kết quả chấm điểm
            filename: tên file (optional)
            
        Returns:
            buffer: BytesIO buffer chứa CSV
        """
        # Tạo DataFrame
        df_info = self.generate_dataframe(cv_info, score_result)
        df_skills = self.generate_skills_dataframe(score_result)
        
        # Xuất ra buffer
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_info.to_excel(writer, sheet_name='Thông tin chung', index=False)
            df_skills.to_excel(writer, sheet_name='Kỹ năng', index=False)
            
            # Thêm sheet gợi ý
            suggestions_df = pd.DataFrame({
                'Gợi ý cải thiện': score_result.get('suggestions', [])
            })
            suggestions_df.to_excel(writer, sheet_name='Gợi ý', index=False)
        
        buffer.seek(0)
        return buffer
    
    def export_batch_to_excel(
        self,
        results: List[Dict],
        job_title: str
    ) -> BytesIO:
        """
        Xuất kết quả batch ra Excel
        
        Args:
            results: danh sách kết quả
            job_title: vị trí ứng tuyển
            
        Returns:
            buffer: BytesIO buffer
        """
        # Tạo DataFrame tổng hợp
        data = []
        for result in results:
            data.append({
                'Xếp hạng': result.get('rank', 0),
                'Họ tên': result.get('cv_name', 'N/A'),
                'Điểm': result['final_score'],
                'Mức độ phù hợp': result['fit_level'],
                'Kỹ năng khớp': result['skill_match']['total_matched'],
                'Kỹ năng thiếu': len(result['skill_match']['missing_required']),
                'Điểm kỹ năng': result['skill_match']['total_score'],
                'Điểm kinh nghiệm': result['breakdown']['experience_score'] / 0.2,
                'Điểm học vấn': result['breakdown']['education_score'] / 0.15
            })
        
        df = pd.DataFrame(data)
        
        # Xuất ra Excel
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Xếp hạng', index=False)
            
            # Format worksheet
            workbook = writer.book
            worksheet = writer.sheets['Xếp hạng']
            
            # Format header
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#667eea',
                'font_color': 'white',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-fit columns
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_len)
        
        buffer.seek(0)
        return buffer
    
    def generate_text_report(
        self,
        cv_info: Dict,
        score_result: Dict
    ) -> str:
        """
        Tạo báo cáo dạng text
        
        Args:
            cv_info: thông tin CV
            score_result: kết quả chấm điểm
            
        Returns:
            report: báo cáo text
        """
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           BÁO CÁO PHÂN TÍCH CV - HỆ THỐNG AI                 ║
╚══════════════════════════════════════════════════════════════╝

📅 Ngày phân tích: {datetime.now().strftime('%d/%m/%Y %H:%M')}

👤 THÔNG TIN ỨNG VIÊN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Họ tên: {cv_info.get('name', 'N/A')}
• Email: {cv_info.get('email', 'N/A')}
• Số điện thoại: {cv_info.get('phone', 'N/A')}
• GPA: {cv_info.get('gpa', 'N/A')}

📊 KẾT QUẢ CHẤM ĐIỂM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Điểm tổng thể: {score_result['final_score']}/100
• Mức độ phù hợp: {score_result['fit_level']}
• Phương pháp: {score_result['score_method']}

📈 CHI TIẾT ĐIỂM SỐ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Kỹ năng kỹ thuật: {score_result['breakdown']['skill_score']:.1f}/40
• Độ phù hợp văn bản: {score_result['breakdown']['text_similarity_score']:.1f}/25
• Kinh nghiệm/Dự án: {score_result['breakdown']['experience_score']:.1f}/20
• Học vấn: {score_result['breakdown']['education_score']:.1f}/15

✅ KỸ NĂNG KHỚP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Kỹ năng bắt buộc ({len(score_result['skill_match']['matched_required'])}/{score_result['skill_match']['total_required']}):
{', '.join(score_result['skill_match']['matched_required'][:10]) if score_result['skill_match']['matched_required'] else 'Không có'}

Kỹ năng ưu tiên ({len(score_result['skill_match']['matched_preferred'])}):
{', '.join(score_result['skill_match']['matched_preferred'][:10]) if score_result['skill_match']['matched_preferred'] else 'Không có'}

❌ KỸ NĂNG CÒN THIẾU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{', '.join(score_result['skill_match']['missing_required'][:10]) if score_result['skill_match']['missing_required'] else 'Không có'}

💡 GỢI Ý CẢI THIỆN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for i, suggestion in enumerate(score_result.get('suggestions', []), 1):
            report += f"{i}. {suggestion}\n"
        
        report += "\n" + "━" * 62 + "\n"
        report += "Báo cáo được tạo bởi CV Analyzer - Hệ thống phân tích CV bằng AI\n"
        
        return report
