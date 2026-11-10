"""
Module tiền xử lý văn bản NLP (hỗ trợ tiếng Việt và tiếng Anh)
"""

import re
import string
from typing import List
import unicodedata


class TextPreprocessor:
    """Class xử lý tiền xử lý văn bản"""
    
    def __init__(self):
        # Stopwords tiếng Việt
        self.vietnamese_stopwords = {
            'và', 'của', 'có', 'được', 'trong', 'là', 'cho', 'với', 'để',
            'các', 'một', 'những', 'này', 'đó', 'khi', 'như', 'từ', 'về',
            'theo', 'hoặc', 'nhưng', 'thì', 'cũng', 'nếu', 'sẽ', 'đã', 'bị',
            'còn', 'rất', 'nhiều', 'hay', 'vào', 'đang', 'lại', 'không'
        }
        
        # Stopwords tiếng Anh
        self.english_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        self.all_stopwords = self.vietnamese_stopwords | self.english_stopwords
    
    def remove_urls(self, text: str) -> str:
        """
        Loại bỏ URLs từ văn bản
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã loại bỏ URLs
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, '', text)
        return text
    
    def remove_emails(self, text: str) -> str:
        """
        Loại bỏ emails từ văn bản
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã loại bỏ emails
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '', text)
        return text
    
    def remove_phone_numbers(self, text: str) -> str:
        """
        Loại bỏ số điện thoại từ văn bản
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã loại bỏ SĐT
        """
        phone_pattern = r'(\+84|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}'
        text = re.sub(phone_pattern, '', text)
        return text
    
    def remove_special_characters(self, text: str, keep_spaces: bool = True) -> str:
        """
        Loại bỏ ký tự đặc biệt
        
        Args:
            text: văn bản đầu vào
            keep_spaces: giữ lại khoảng trắng
            
        Returns:
            text: văn bản đã loại bỏ ký tự đặc biệt
        """
        if keep_spaces:
            # Giữ lại chữ cái, số và khoảng trắng
            text = re.sub(r'[^a-zA-Z0-9\sÀ-ỹ]', ' ', text)
        else:
            # Chỉ giữ lại chữ cái và số
            text = re.sub(r'[^a-zA-Z0-9À-ỹ]', '', text)
        
        return text
    
    def remove_extra_whitespace(self, text: str) -> str:
        """
        Loại bỏ khoảng trắng thừa
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã chuẩn hóa khoảng trắng
        """
        # Thay thế nhiều khoảng trắng liên tiếp bằng 1 khoảng trắng
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def normalize_unicode(self, text: str) -> str:
        """
        Chuẩn hóa Unicode (quan trọng cho tiếng Việt)
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã chuẩn hóa
        """
        # Chuẩn hóa về dạng NFC (Canonical Composition)
        text = unicodedata.normalize('NFC', text)
        return text
    
    def to_lowercase(self, text: str) -> str:
        """
        Chuyển văn bản về chữ thường
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản chữ thường
        """
        return text.lower()
    
    def remove_stopwords(self, text: str) -> str:
        """
        Loại bỏ stopwords (từ dừng)
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã loại bỏ stopwords
        """
        words = text.split()
        filtered_words = [
            word for word in words 
            if word.lower() not in self.all_stopwords
        ]
        return ' '.join(filtered_words)
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tách từ (tokenization) đơn giản
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            tokens: danh sách các từ
        """
        # Tách theo khoảng trắng
        tokens = text.split()
        return tokens
    
    def preprocess(
        self, 
        text: str,
        lowercase: bool = True,
        remove_stopwords: bool = False,
        remove_special_chars: bool = True,
        remove_personal_info: bool = True
    ) -> str:
        """
        Pipeline xử lý văn bản đầy đủ
        
        Args:
            text: văn bản đầu vào
            lowercase: chuyển về chữ thường
            remove_stopwords: loại bỏ stopwords
            remove_special_chars: loại bỏ ký tự đặc biệt
            remove_personal_info: loại bỏ thông tin cá nhân
            
        Returns:
            text: văn bản đã xử lý
        """
        if not text:
            return ""
        
        # Chuẩn hóa Unicode
        text = self.normalize_unicode(text)
        
        # Loại bỏ thông tin cá nhân
        if remove_personal_info:
            text = self.remove_urls(text)
            text = self.remove_emails(text)
            text = self.remove_phone_numbers(text)
        
        # Loại bỏ ký tự đặc biệt
        if remove_special_chars:
            text = self.remove_special_characters(text, keep_spaces=True)
        
        # Chuyển về chữ thường
        if lowercase:
            text = self.to_lowercase(text)
        
        # Loại bỏ khoảng trắng thừa
        text = self.remove_extra_whitespace(text)
        
        # Loại bỏ stopwords
        if remove_stopwords:
            text = self.remove_stopwords(text)
            text = self.remove_extra_whitespace(text)
        
        return text
    
    def preprocess_for_matching(self, text: str) -> str:
        """
        Xử lý văn bản cho việc matching/scoring
        (giữ lại nhiều thông tin hơn, không xóa stopwords)
        
        Args:
            text: văn bản đầu vào
            
        Returns:
            text: văn bản đã xử lý
        """
        return self.preprocess(
            text,
            lowercase=True,
            remove_stopwords=False,
            remove_special_chars=True,
            remove_personal_info=False
        )
    
    def extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """
        Trích xuất từ khóa quan trọng từ văn bản
        
        Args:
            text: văn bản đầu vào
            top_n: số từ khóa cần lấy
            
        Returns:
            keywords: danh sách từ khóa
        """
        # Xử lý văn bản
        processed_text = self.preprocess(
            text,
            lowercase=True,
            remove_stopwords=True,
            remove_special_chars=True,
            remove_personal_info=True
        )
        
        # Tách từ
        words = processed_text.split()
        
        # Đếm tần suất
        word_freq = {}
        for word in words:
            if len(word) > 2:  # Chỉ lấy từ có độ dài > 2
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sắp xếp theo tần suất
        sorted_words = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Lấy top N
        keywords = [word for word, freq in sorted_words[:top_n]]
        
        return keywords
