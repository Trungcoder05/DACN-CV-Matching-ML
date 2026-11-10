"""
Module trích xuất thông tin từ CV (PDF, DOCX)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import io

from .skills_db import get_all_skills


class CVExtractor:
    """Class xử lý trích xuất thông tin từ CV"""
    
    def __init__(self):
        self.skills_list = [s.lower() for s in get_all_skills()]
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Trích xuất text từ PDF, hỗ trợ cả PDF text và PDF scan (OCR)
        
        Args:
            file_path: đường dẫn file PDF
            
        Returns:
            text: nội dung text đã trích xuất
        """
        text = ""
        
        try:
            # Thử trích xuất text thông thường trước
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Nếu text quá ít, có thể là PDF scan, thử OCR
            if len(text.strip()) < 100:
                text = self._extract_text_with_ocr(file_path)
                
        except Exception as e:
            print(f"Lỗi khi đọc PDF: {e}")
            # Fallback sang PyMuPDF
            try:
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            except Exception as e2:
                print(f"Lỗi khi dùng PyMuPDF: {e2}")
                
        return text.strip()
    
    def _extract_text_with_ocr(self, file_path: str) -> str:
        """
        Trích xuất text từ PDF scan bằng OCR (Tesseract)
        
        Args:
            file_path: đường dẫn file PDF
            
        Returns:
            text: nội dung text sau OCR
        """
        try:
            import pytesseract
            
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # OCR với hỗ trợ tiếng Việt
                page_text = pytesseract.image_to_string(
                    image, 
                    lang='vie+eng',
                    config='--psm 6'
                )
                text += page_text + "\n"
            
            doc.close()
            return text
            
        except ImportError:
            print("Tesseract chưa được cài đặt. Vui lòng cài đặt để sử dụng OCR.")
            return ""
        except Exception as e:
            print(f"Lỗi khi OCR: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Trích xuất text từ DOCX
        
        Args:
            file_path: đường dẫn file DOCX
            
        Returns:
            text: nội dung text đã trích xuất
        """
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Trích xuất text từ tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            print(f"Lỗi khi đọc DOCX: {e}")
            return ""
    
    def extract_text(self, file_path: str, file_extension: str) -> str:
        """
        Trích xuất text từ file CV
        
        Args:
            file_path: đường dẫn file
            file_extension: phần mở rộng file (.pdf hoặc .docx)
            
        Returns:
            text: nội dung text
        """
        if file_extension.lower() == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension.lower() in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            return ""
    
    def extract_name(self, text: str) -> Optional[str]:
        """
        Trích xuất tên từ CV (thường ở đầu CV)
        
        Args:
            text: nội dung CV
            
        Returns:
            name: họ tên hoặc None
        """
        lines = text.split('\n')
        
        # Tên thường ở 3 dòng đầu tiên
        for line in lines[:5]:
            line = line.strip()
            # Tên thường là chữ in hoa hoặc có độ dài 10-50 ký tự
            if line and len(line) >= 5 and len(line) <= 50:
                # Loại bỏ các dòng có số điện thoại, email
                if not re.search(r'\d{3,}|@|gmail|email|phone|số điện thoại', line.lower()):
                    # Kiểm tra có phải tên người (chứa chữ cái)
                    if re.search(r'[a-zA-ZÀ-ỹ\s]+', line) and line.isupper():
                        return line.title()
                    elif re.search(r'^[A-ZÀ-Ỹ][a-zà-ỹ]+(\s[A-ZÀ-Ỹ][a-zà-ỹ]+)+', line):
                        return line
        
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """
        Trích xuất email từ CV
        
        Args:
            text: nội dung CV
            
        Returns:
            email: địa chỉ email hoặc None
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            return emails[0]
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """
        Trích xuất số điện thoại từ CV
        
        Args:
            text: nội dung CV
            
        Returns:
            phone: số điện thoại hoặc None
        """
        # Các pattern phổ biến cho SĐT Việt Nam
        phone_patterns = [
            r'(\+84|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}',
            r'\b0\d{9,10}\b',
            r'\(\+84\)\s?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                phone = phones[0]
                # Chuẩn hóa
                phone = re.sub(r'[\s.-]', '', str(phone))
                return phone
        
        return None
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """
        Trích xuất thông tin học vấn
        
        Args:
            text: nội dung CV
            
        Returns:
            education: danh sách học vấn
        """
        education_list = []
        
        # Tìm các từ khóa về giáo dục
        edu_keywords = [
            'đại học', 'university', 'cao đẳng', 'college', 'học viện',
            'trường', 'school', 'bachelor', 'master', 'phd', 'tiến sĩ', 'thạc sĩ'
        ]
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in edu_keywords):
                edu_info = {
                    'school': line.strip(),
                    'details': ''
                }
                
                # Lấy thêm vài dòng tiếp theo
                if i + 1 < len(lines):
                    edu_info['details'] = lines[i + 1].strip()
                
                education_list.append(edu_info)
        
        return education_list
    
    def extract_gpa(self, text: str) -> Optional[str]:
        """
        Trích xuất GPA từ CV
        
        Args:
            text: nội dung CV
            
        Returns:
            gpa: điểm GPA hoặc None
        """
        # Pattern cho GPA
        gpa_patterns = [
            r'gpa[\s:]*(\d+\.?\d*)\s*/\s*(\d+\.?\d*)',
            r'điểm\s*trung\s*bình[\s:]*(\d+\.?\d*)',
            r'cpa[\s:]*(\d+\.?\d*)\s*/\s*(\d+\.?\d*)'
        ]
        
        text_lower = text.lower()
        
        for pattern in gpa_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"{matches[0][0]}/{matches[0][1]}"
                else:
                    return matches[0]
        
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Trích xuất kỹ năng từ CV
        
        Args:
            text: nội dung CV
            
        Returns:
            skills: danh sách kỹ năng tìm thấy
        """
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skills_list:
            # Tìm kiếm từng kỹ năng (case insensitive, whole word)
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                # Thêm vào với format gốc (viết hoa đúng)
                original_skill = next(
                    (s for s in get_all_skills() if s.lower() == skill),
                    skill
                )
                if original_skill not in found_skills:
                    found_skills.append(original_skill)
        
        return found_skills
    
    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """
        Trích xuất ngoại ngữ từ CV
        
        Args:
            text: nội dung CV
            
        Returns:
            languages: danh sách ngoại ngữ và trình độ
        """
        languages = []
        
        # Các ngôn ngữ phổ biến
        lang_keywords = {
            'english': 'Tiếng Anh',
            'tiếng anh': 'Tiếng Anh',
            'japanese': 'Tiếng Nhật',
            'tiếng nhật': 'Tiếng Nhật',
            'chinese': 'Tiếng Trung',
            'tiếng trung': 'Tiếng Trung',
            'korean': 'Tiếng Hàn',
            'tiếng hàn': 'Tiếng Hàn',
            'french': 'Tiếng Pháp',
            'tiếng pháp': 'Tiếng Pháp'
        }
        
        # Trình độ
        proficiency_keywords = [
            'toeic', 'ielts', 'toefl', 'n1', 'n2', 'n3', 'n4', 'n5',
            'hsk', 'native', 'fluent', 'intermediate', 'basic',
            'thành thạo', 'trung bình', 'cơ bản'
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            for keyword, lang_name in lang_keywords.items():
                if keyword in line_lower:
                    level = 'Không xác định'
                    
                    # Tìm trình độ
                    for prof in proficiency_keywords:
                        if prof in line_lower:
                            # Trích xuất điểm số nếu có
                            score_match = re.search(rf'{prof}[\s:]*(\d+)', line_lower)
                            if score_match:
                                level = f"{prof.upper()} {score_match.group(1)}"
                            else:
                                level = prof.title()
                            break
                    
                    languages.append({
                        'language': lang_name,
                        'level': level
                    })
        
        return languages
    
    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """
        Trích xuất thông tin dự án
        
        Args:
            text: nội dung CV
            
        Returns:
            projects: danh sách dự án
        """
        projects = []
        
        # Tìm section dự án
        project_keywords = ['dự án', 'project', 'projects', 'đồ án']
        
        lines = text.split('\n')
        in_project_section = False
        current_project = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Phát hiện bắt đầu section dự án
            if any(keyword in line_lower for keyword in project_keywords):
                in_project_section = True
                continue
            
            # Phát hiện kết thúc section (gặp section khác)
            if in_project_section and any(
                keyword in line_lower 
                for keyword in ['kinh nghiệm', 'experience', 'học vấn', 'education', 'kỹ năng', 'skills']
            ):
                in_project_section = False
            
            # Trích xuất thông tin dự án
            if in_project_section and line.strip():
                # Dòng có thể là tên dự án (thường in đậm hoặc có dấu -, •)
                if line.startswith(('-', '•', '●', '*')) or (line and line[0].isupper()):
                    if current_project:
                        projects.append(current_project)
                    
                    current_project = {
                        'name': line.strip('- •●*').strip(),
                        'description': ''
                    }
                elif current_project:
                    # Mô tả dự án
                    current_project['description'] += ' ' + line.strip()
        
        # Thêm dự án cuối cùng
        if current_project:
            projects.append(current_project)
        
        return projects[:5]  # Giới hạn 5 dự án
    
    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """
        Trích xuất kinh nghiệm làm việc
        
        Args:
            text: nội dung CV
            
        Returns:
            experience: danh sách kinh nghiệm
        """
        experiences = []
        
        # Tìm section kinh nghiệm
        exp_keywords = ['kinh nghiệm', 'experience', 'work experience', 'employment']
        
        lines = text.split('\n')
        in_exp_section = False
        current_exp = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Phát hiện bắt đầu section kinh nghiệm
            if any(keyword in line_lower for keyword in exp_keywords):
                in_exp_section = True
                continue
            
            # Phát hiện kết thúc section
            if in_exp_section and any(
                keyword in line_lower 
                for keyword in ['dự án', 'project', 'học vấn', 'education', 'kỹ năng', 'skills']
            ):
                in_exp_section = False
            
            # Trích xuất kinh nghiệm
            if in_exp_section and line.strip():
                if line.startswith(('-', '•', '●', '*')) or (line and line[0].isupper()):
                    if current_exp:
                        experiences.append(current_exp)
                    
                    current_exp = {
                        'position': line.strip('- •●*').strip(),
                        'description': ''
                    }
                elif current_exp:
                    current_exp['description'] += ' ' + line.strip()
        
        if current_exp:
            experiences.append(current_exp)
        
        return experiences[:5]
    
    def extract_all_info(self, file_path: str) -> Dict:
        """
        Trích xuất toàn bộ thông tin từ CV
        
        Args:
            file_path: đường dẫn file CV
            
        Returns:
            info: dictionary chứa tất cả thông tin
        """
        file_extension = Path(file_path).suffix
        
        # Trích xuất text
        text = self.extract_text(file_path, file_extension)
        
        if not text or len(text) < 50:
            raise ValueError("Không thể trích xuất text từ CV hoặc CV quá ngắn")
        
        # Trích xuất các thông tin
        info = {
            'raw_text': text,
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'education': self.extract_education(text),
            'gpa': self.extract_gpa(text),
            'skills': self.extract_skills(text),
            'languages': self.extract_languages(text),
            'projects': self.extract_projects(text),
            'experience': self.extract_experience(text)
        }
        
        return info
