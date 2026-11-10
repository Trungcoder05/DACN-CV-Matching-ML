"""
Module chấm điểm và đánh giá mức độ phù hợp của CV với vị trí
"""

import os
import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills_db import (
    get_job_info,
    get_required_skills_for_job,
    get_preferred_skills_for_job
)
from .preprocess import TextPreprocessor


class CVScorer:
    """Class chấm điểm CV"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Khởi tạo scorer
        
        Args:
            model_path: đường dẫn đến model đã train (optional)
        """
        self.preprocessor = TextPreprocessor()
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.9
        )
        
        # Load model nếu có
        self.model = None
        self.model_vectorizer = None
        
        if model_path and os.path.exists(model_path):
            try:
                model_data = joblib.load(model_path)
                self.model = model_data.get('model')
                self.model_vectorizer = model_data.get('vectorizer')
                print(f"✅ Đã load model từ {model_path}")
            except Exception as e:
                print(f"⚠️ Không thể load model: {e}")
                print("Sẽ sử dụng phương pháp fallback (TF-IDF + rule-based)")
    
    def calculate_skill_match_score(
        self,
        cv_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Dict:
        """
        Tính điểm khớp kỹ năng
        
        Args:
            cv_skills: kỹ năng từ CV
            required_skills: kỹ năng bắt buộc
            preferred_skills: kỹ năng ưu tiên
            
        Returns:
            score_info: thông tin điểm và kỹ năng
        """
        # Chuẩn hóa để so sánh
        cv_skills_lower = [s.lower() for s in cv_skills]
        required_lower = [s.lower() for s in required_skills]
        preferred_lower = [s.lower() for s in preferred_skills]
        
        # Tìm kỹ năng khớp
        matched_required = []
        for skill in required_skills:
            if skill.lower() in cv_skills_lower:
                matched_required.append(skill)
        
        matched_preferred = []
        for skill in preferred_skills:
            if skill.lower() in cv_skills_lower:
                matched_preferred.append(skill)
        
        # Tìm kỹ năng thiếu
        missing_required = [
            skill for skill in required_skills 
            if skill.lower() not in cv_skills_lower
        ]
        
        missing_preferred = [
            skill for skill in preferred_skills 
            if skill.lower() not in cv_skills_lower
        ]
        
        # Tính điểm
        required_score = 0
        if required_skills:
            required_score = (len(matched_required) / len(required_skills)) * 100
        
        preferred_score = 0
        if preferred_skills:
            preferred_score = (len(matched_preferred) / len(preferred_skills)) * 100
        
        # Điểm tổng (required quan trọng hơn)
        total_score = (required_score * 0.7) + (preferred_score * 0.3)
        
        return {
            'total_score': round(total_score, 2),
            'required_score': round(required_score, 2),
            'preferred_score': round(preferred_score, 2),
            'matched_required': matched_required,
            'matched_preferred': matched_preferred,
            'missing_required': missing_required,
            'missing_preferred': missing_preferred,
            'total_matched': len(matched_required) + len(matched_preferred),
            'total_required': len(required_skills),
            'total_preferred': len(preferred_skills)
        }
    
    def calculate_text_similarity(
        self,
        cv_text: str,
        job_description: str
    ) -> float:
        """
        Tính độ tương đồng giữa CV và mô tả công việc bằng TF-IDF
        
        Args:
            cv_text: nội dung CV
            job_description: mô tả công việc
            
        Returns:
            similarity: điểm tương đồng (0-100)
        """
        # Tiền xử lý văn bản
        cv_processed = self.preprocessor.preprocess_for_matching(cv_text)
        job_processed = self.preprocessor.preprocess_for_matching(job_description)
        
        if not cv_processed or not job_processed:
            return 0.0
        
        try:
            # Tính TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform([cv_processed, job_processed])
            
            # Tính cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Chuyển về thang điểm 100
            similarity_score = similarity * 100
            
            return round(similarity_score, 2)
            
        except Exception as e:
            print(f"Lỗi khi tính similarity: {e}")
            return 0.0
    
    def calculate_experience_score(
        self,
        experience: List[Dict],
        projects: List[Dict]
    ) -> float:
        """
        Tính điểm kinh nghiệm và dự án
        
        Args:
            experience: danh sách kinh nghiệm
            projects: danh sách dự án
            
        Returns:
            score: điểm kinh nghiệm (0-100)
        """
        score = 0
        
        # Điểm cho kinh nghiệm (tối đa 50 điểm)
        if experience:
            exp_count = len(experience)
            if exp_count >= 3:
                score += 50
            elif exp_count == 2:
                score += 40
            elif exp_count == 1:
                score += 25
        
        # Điểm cho dự án (tối đa 50 điểm)
        if projects:
            project_count = len(projects)
            if project_count >= 5:
                score += 50
            elif project_count >= 3:
                score += 40
            elif project_count >= 2:
                score += 30
            elif project_count == 1:
                score += 20
        
        return min(score, 100)
    
    def calculate_education_score(
        self,
        education: List[Dict],
        gpa: Optional[str]
    ) -> float:
        """
        Tính điểm học vấn
        
        Args:
            education: danh sách học vấn
            gpa: điểm GPA
            
        Returns:
            score: điểm học vấn (0-100)
        """
        score = 0
        
        # Điểm cho bằng cấp (60 điểm)
        if education:
            # Có thông tin đại học/cao đẳng
            score += 60
            
            # Kiểm tra các từ khóa uy tín
            edu_text = ' '.join([
                f"{e.get('school', '')} {e.get('details', '')}" 
                for e in education
            ]).lower()
            
            prestigious_keywords = [
                'bách khoa', 'khoa học tự nhiên', 'kinh tế quốc dân',
                'ngoại thương', 'technology', 'polytechnic', 'mit', 'stanford'
            ]
            
            if any(keyword in edu_text for keyword in prestigious_keywords):
                score += 10
        
        # Điểm cho GPA (30 điểm)
        if gpa:
            try:
                # Trích xuất số GPA
                gpa_str = str(gpa).replace(',', '.')
                gpa_match = gpa_str.split('/')[0].strip()
                gpa_value = float(gpa_match)
                
                # Giả sử thang điểm 4.0
                if gpa_value > 4:
                    gpa_value = gpa_value / 10 * 4  # Chuyển đổi từ thang 10
                
                if gpa_value >= 3.6:
                    score += 30
                elif gpa_value >= 3.2:
                    score += 25
                elif gpa_value >= 2.8:
                    score += 20
                elif gpa_value >= 2.5:
                    score += 15
                else:
                    score += 10
                    
            except (ValueError, IndexError):
                pass
        
        return min(score, 100)
    
    def predict_with_model(
        self,
        cv_text: str,
        job_title: str
    ) -> Optional[float]:
        """
        Dự đoán điểm bằng ML model (nếu có)
        
        Args:
            cv_text: nội dung CV
            job_title: vị trí ứng tuyển
            
        Returns:
            score: điểm dự đoán hoặc None nếu không có model
        """
        if self.model is None or self.model_vectorizer is None:
            return None
        
        try:
            # Tiền xử lý
            processed_text = self.preprocessor.preprocess_for_matching(cv_text)
            
            # Thêm job title vào text để model học được context
            combined_text = f"{processed_text} {job_title.lower()}"
            
            # Vectorize
            X = self.model_vectorizer.transform([combined_text])
            
            # Dự đoán
            prediction = self.model.predict(X)[0]
            
            # Đảm bảo điểm trong khoảng 0-100
            score = max(0, min(100, prediction))
            
            return round(score, 2)
            
        except Exception as e:
            print(f"Lỗi khi dự đoán với model: {e}")
            return None
    
    def score_cv(
        self,
        cv_info: Dict,
        job_title: str,
        custom_job_description: Optional[str] = None
    ) -> Dict:
        """
        Chấm điểm tổng thể cho CV
        
        Args:
            cv_info: thông tin đã trích xuất từ CV
            job_title: vị trí ứng tuyển
            custom_job_description: mô tả công việc tùy chỉnh (optional)
            
        Returns:
            result: kết quả chấm điểm chi tiết
        """
        # Lấy thông tin vị trí
        job_info = get_job_info(job_title)
        required_skills = get_required_skills_for_job(job_title)
        preferred_skills = get_preferred_skills_for_job(job_title)
        
        # 1. Điểm khớp kỹ năng (40%)
        skill_match = self.calculate_skill_match_score(
            cv_info.get('skills', []),
            required_skills,
            preferred_skills
        )
        skill_score = skill_match['total_score'] * 0.4
        
        # 2. Điểm tương đồng văn bản (25%)
        job_desc = custom_job_description or job_info.get('description', '')
        job_desc_full = f"{job_desc} {' '.join(required_skills)} {' '.join(preferred_skills)}"
        
        text_similarity = self.calculate_text_similarity(
            cv_info.get('raw_text', ''),
            job_desc_full
        )
        text_score = text_similarity * 0.25
        
        # 3. Điểm kinh nghiệm/dự án (20%)
        exp_score = self.calculate_experience_score(
            cv_info.get('experience', []),
            cv_info.get('projects', [])
        ) * 0.2
        
        # 4. Điểm học vấn (15%)
        edu_score = self.calculate_education_score(
            cv_info.get('education', []),
            cv_info.get('gpa')
        ) * 0.15
        
        # Tổng điểm (rule-based)
        total_score_rule = skill_score + text_score + exp_score + edu_score
        
        # Thử dự đoán bằng ML model
        model_score = self.predict_with_model(
            cv_info.get('raw_text', ''),
            job_title
        )
        
        # Nếu có model, kết hợp cả 2 (70% model, 30% rule-based)
        if model_score is not None:
            final_score = (model_score * 0.7) + (total_score_rule * 0.3)
            score_method = "ML Model + Rule-based"
        else:
            final_score = total_score_rule
            score_method = "Rule-based (TF-IDF + Skills)"
        
        # Phân loại mức độ phù hợp
        if final_score >= 80:
            fit_level = "Rất phù hợp"
            fit_class = "excellent"
        elif final_score >= 65:
            fit_level = "Phù hợp"
            fit_class = "good"
        elif final_score >= 50:
            fit_level = "Cần cải thiện"
            fit_class = "fair"
        else:
            fit_level = "Chưa phù hợp"
            fit_class = "poor"
        
        # Tạo radar chart data
        radar_data = {
            'Kỹ năng kỹ thuật': skill_match['total_score'],
            'Kinh nghiệm/Dự án': self.calculate_experience_score(
                cv_info.get('experience', []),
                cv_info.get('projects', [])
            ),
            'Học vấn': self.calculate_education_score(
                cv_info.get('education', []),
                cv_info.get('gpa')
            ),
            'Độ phù hợp văn bản': text_similarity,
            'Kỹ năng bắt buộc': skill_match['required_score']
        }
        
        # Gợi ý cải thiện
        suggestions = self._generate_suggestions(
            cv_info,
            skill_match,
            job_title
        )
        
        return {
            'final_score': round(final_score, 2),
            'fit_level': fit_level,
            'fit_class': fit_class,
            'score_method': score_method,
            'breakdown': {
                'skill_score': round(skill_score, 2),
                'text_similarity_score': round(text_score, 2),
                'experience_score': round(exp_score, 2),
                'education_score': round(edu_score, 2)
            },
            'skill_match': skill_match,
            'radar_data': radar_data,
            'suggestions': suggestions,
            'job_info': job_info
        }
    
    def _generate_suggestions(
        self,
        cv_info: Dict,
        skill_match: Dict,
        job_title: str
    ) -> List[str]:
        """
        Tạo gợi ý cải thiện CV
        
        Args:
            cv_info: thông tin CV
            skill_match: kết quả matching kỹ năng
            job_title: vị trí ứng tuyển
            
        Returns:
            suggestions: danh sách gợi ý
        """
        suggestions = []
        
        # Gợi ý về kỹ năng thiếu
        missing_required = skill_match['missing_required']
        if missing_required:
            top_missing = missing_required[:5]
            suggestions.append(
                f"📚 **Học thêm kỹ năng bắt buộc**: {', '.join(top_missing)}"
            )
        
        missing_preferred = skill_match['missing_preferred']
        if missing_preferred and len(missing_required) < 3:
            top_missing_pref = missing_preferred[:3]
            suggestions.append(
                f"💡 **Kỹ năng ưu tiên nên có**: {', '.join(top_missing_pref)}"
            )
        
        # Gợi ý về dự án
        projects = cv_info.get('projects', [])
        if len(projects) < 3:
            suggestions.append(
                "🚀 **Thêm dự án cá nhân**: Xây dựng 2-3 dự án thực tế để showcase kỹ năng"
            )
        
        # Gợi ý về kinh nghiệm
        experience = cv_info.get('experience', [])
        if not experience:
            suggestions.append(
                "💼 **Tìm kiếm kinh nghiệm**: Thực tập, freelance hoặc contribute vào open source"
            )
        
        # Gợi ý về GPA
        if not cv_info.get('gpa'):
            suggestions.append(
                "🎓 **Thêm GPA**: Ghi rõ điểm trung bình nếu GPA >= 3.0/4.0 hoặc 7.0/10"
            )
        
        # Gợi ý về chứng chỉ
        languages = cv_info.get('languages', [])
        if not languages:
            suggestions.append(
                "🌏 **Chứng chỉ ngoại ngữ**: TOEIC, IELTS giúp tăng cơ hội được nhận"
            )
        
        # Gợi ý cụ thể theo vị trí
        if 'Backend' in job_title and 'Docker' not in cv_info.get('skills', []):
            suggestions.append(
                "🐳 **Docker & Containerization**: Kỹ năng quan trọng cho Backend Developer"
            )
        
        if 'Frontend' in job_title and 'TypeScript' not in cv_info.get('skills', []):
            suggestions.append(
                "⚡ **TypeScript**: Đang trở thành standard cho Frontend hiện đại"
            )
        
        if 'AI' in job_title or 'ML' in job_title:
            if 'TensorFlow' not in cv_info.get('skills', []) and 'PyTorch' not in cv_info.get('skills', []):
                suggestions.append(
                    "🤖 **Deep Learning Framework**: Học TensorFlow hoặc PyTorch"
                )
        
        # Giới hạn 6 gợi ý
        return suggestions[:6]
    
    def batch_score_cvs(
        self,
        cv_info_list: List[Dict],
        job_title: str,
        custom_job_description: Optional[str] = None
    ) -> List[Dict]:
        """
        Chấm điểm nhiều CV cùng lúc
        
        Args:
            cv_info_list: danh sách thông tin CV
            job_title: vị trí ứng tuyển
            custom_job_description: mô tả công việc tùy chỉnh
            
        Returns:
            results: danh sách kết quả đã sắp xếp theo điểm
        """
        results = []
        
        for idx, cv_info in enumerate(cv_info_list):
            try:
                score_result = self.score_cv(cv_info, job_title, custom_job_description)
                score_result['cv_index'] = idx
                score_result['cv_name'] = cv_info.get('name', f'CV_{idx+1}')
                results.append(score_result)
            except Exception as e:
                print(f"Lỗi khi chấm điểm CV {idx+1}: {e}")
        
        # Sắp xếp theo điểm giảm dần
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Thêm ranking
        for rank, result in enumerate(results, 1):
            result['rank'] = rank
        
        return results
