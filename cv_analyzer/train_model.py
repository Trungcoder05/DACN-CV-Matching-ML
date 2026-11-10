"""
Script huấn luyện mô hình Machine Learning cho việc chấm điểm CV
Tự động tạo synthetic dataset nếu chưa có dữ liệu thật
"""

import os
import random
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns

from core.skills_db import get_all_job_titles, get_required_skills_for_job, get_preferred_skills_for_job
from core.preprocess import TextPreprocessor


class CVModelTrainer:
    """Class huấn luyện mô hình"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.vectorizer = None
    
    def generate_synthetic_cv(
        self,
        job_title: str,
        score_range: tuple = (0, 100)
    ) -> tuple:
        """
        Tạo CV synthetic cho một vị trí
        
        Args:
            job_title: vị trí công việc
            score_range: khoảng điểm (min, max)
            
        Returns:
            (cv_text, score): CV text và điểm mục tiêu
        """
        required_skills = get_required_skills_for_job(job_title)
        preferred_skills = get_preferred_skills_for_job(job_title)
        
        # Tạo điểm ngẫu nhiên
        target_score = random.uniform(score_range[0], score_range[1])
        
        # Templates
        names = ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C", "Phạm Thị D", "Hoàng Văn E"]
        universities = [
            "Đại học Bách Khoa", "Đại học Khoa học Tự nhiên",
            "Đại học Công nghệ", "Đại học FPT", "Đại học RMIT"
        ]
        
        # Tạo kỹ năng dựa trên target score
        num_required = int((target_score / 100) * len(required_skills))
        num_preferred = int((target_score / 100) * len(preferred_skills) * 0.5)
        
        selected_required = random.sample(required_skills, min(num_required, len(required_skills)))
        selected_preferred = random.sample(preferred_skills, min(num_preferred, len(preferred_skills)))
        
        # Random thêm skills
        all_skills = selected_required + selected_preferred
        random.shuffle(all_skills)
        
        # Tạo CV text
        cv_parts = [
            f"HỒ SƠ ỨNG VIÊN",
            f"Họ tên: {random.choice(names)}",
            f"Email: candidate{random.randint(1, 999)}@email.com",
            f"Điện thoại: {random.randint(900000000, 999999999)}",
            "",
            "HỌC VẤN",
            f"{random.choice(universities)}",
            f"Chuyên ngành: Công nghệ thông tin",
            f"GPA: {random.uniform(2.5, 4.0):.2f}/4.0",
            "",
            "KỸ NĂNG"
        ]
        
        # Thêm kỹ năng
        cv_parts.append(", ".join(all_skills))
        cv_parts.append("")
        
        # Thêm kinh nghiệm/dự án dựa trên điểm
        if target_score > 70:
            cv_parts.extend([
                "DỰ ÁN",
                "• Dự án 1: Xây dựng hệ thống quản lý với " + ", ".join(all_skills[:3]),
                "• Dự án 2: Phát triển ứng dụng sử dụng " + ", ".join(all_skills[3:6]),
                "• Dự án 3: Nghiên cứu và triển khai giải pháp với " + ", ".join(all_skills[6:9]),
                "",
                "KINH NGHIỆM",
                f"• Thực tập sinh {job_title} - Công ty ABC (6 tháng)",
                f"  Sử dụng: " + ", ".join(all_skills[:5])
            ])
        elif target_score > 50:
            cv_parts.extend([
                "DỰ ÁN",
                "• Dự án 1: " + ", ".join(all_skills[:4]),
                "• Dự án 2: " + ", ".join(all_skills[4:8]),
            ])
        
        # Thêm ngoại ngữ
        if target_score > 60:
            cv_parts.extend([
                "",
                "NGOẠI NGỮ",
                f"• Tiếng Anh: TOEIC {random.randint(600, 950)}"
            ])
        
        cv_text = "\n".join(cv_parts)
        
        # Thêm job title để model học context
        cv_text += f"\n\nỨng tuyển vị trí: {job_title}"
        
        return cv_text, target_score
    
    def generate_dataset(self, samples_per_job: int = 100) -> pd.DataFrame:
        """
        Tạo synthetic dataset
        
        Args:
            samples_per_job: số CV mẫu cho mỗi vị trí
            
        Returns:
            df: DataFrame chứa dataset
        """
        print("🔄 Đang tạo synthetic dataset...")
        
        job_titles = get_all_job_titles()
        data = []
        
        for job_title in job_titles:
            print(f"  📝 Tạo {samples_per_job} CV cho vị trí: {job_title}")
            
            for _ in range(samples_per_job):
                # Tạo CV với phân bố điểm đa dạng
                score_range = random.choice([
                    (0, 40),    # 20% CV yếu
                    (40, 65),   # 30% CV trung bình
                    (65, 85),   # 40% CV khá
                    (85, 100)   # 10% CV xuất sắc
                ])
                
                cv_text, score = self.generate_synthetic_cv(job_title, score_range)
                
                data.append({
                    'cv_text': cv_text,
                    'job_title': job_title,
                    'score': score
                })
        
        df = pd.DataFrame(data)
        
        print(f"✅ Đã tạo {len(df)} mẫu CV synthetic")
        print(f"   Điểm trung bình: {df['score'].mean():.2f}")
        print(f"   Điểm min: {df['score'].min():.2f}")
        print(f"   Điểm max: {df['score'].max():.2f}")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """
        Chuẩn bị features cho training
        
        Args:
            df: DataFrame chứa dữ liệu
            
        Returns:
            (X, y): features và labels
        """
        print("\n🔄 Đang tiền xử lý và vectorize...")
        
        # Tiền xử lý text
        df['processed_text'] = df['cv_text'].apply(
            lambda x: self.preprocessor.preprocess_for_matching(x)
        )
        
        # TF-IDF vectorization
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        X = self.vectorizer.fit_transform(df['processed_text'])
        y = df['score'].values
        
        print(f"✅ Shape của features: {X.shape}")
        print(f"   Số features: {X.shape[1]}")
        print(f"   Số samples: {X.shape[0]}")
        
        return X, y
    
    def train_models(self, X_train, y_train, X_test, y_test):
        """
        Huấn luyện nhiều mô hình và so sánh
        
        Args:
            X_train, y_train: training data
            X_test, y_test: test data
        """
        print("\n🚀 Bắt đầu huấn luyện các mô hình...\n")
        
        # Định nghĩa các mô hình
        models = {
            'Ridge Regression': Ridge(alpha=1.0),
            'Random Forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            ),
            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        results = []
        
        for name, model in models.items():
            print(f"⚙️  Đang huấn luyện {name}...")
            
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Evaluate
            train_mse = mean_squared_error(y_train, y_pred_train)
            test_mse = mean_squared_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            
            # Cross validation
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=5,
                scoring='r2',
                n_jobs=-1
            )
            
            results.append({
                'Model': name,
                'Train MSE': train_mse,
                'Test MSE': test_mse,
                'Train R²': train_r2,
                'Test R²': test_r2,
                'Test MAE': test_mae,
                'CV R² Mean': cv_scores.mean(),
                'CV R² Std': cv_scores.std()
            })
            
            self.models[name] = model
            
            print(f"   ✓ Test R²: {test_r2:.4f}")
            print(f"   ✓ Test MAE: {test_mae:.2f}")
            print(f"   ✓ CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})\n")
        
        # Tạo bảng so sánh
        results_df = pd.DataFrame(results)
        print("\n📊 SO SÁNH CÁC MÔ HÌNH")
        print("=" * 80)
        print(results_df.to_string(index=False))
        print("=" * 80)
        
        # Chọn model tốt nhất (theo Test R²)
        best_idx = results_df['Test R²'].idxmax()
        self.best_model_name = results_df.loc[best_idx, 'Model']
        self.best_model = self.models[self.best_model_name]
        
        print(f"\n🏆 Model tốt nhất: {self.best_model_name}")
        print(f"   R² Score: {results_df.loc[best_idx, 'Test R²']:.4f}")
        print(f"   MAE: {results_df.loc[best_idx, 'Test MAE']:.2f}")
        
        return results_df
    
    def save_model(self, path: str = 'models/cv_scorer_model.pkl'):
        """
        Lưu model đã train
        
        Args:
            path: đường dẫn lưu model
        """
        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Lưu model và vectorizer
        model_data = {
            'model': self.best_model,
            'vectorizer': self.vectorizer,
            'model_name': self.best_model_name
        }
        
        joblib.dump(model_data, path)
        print(f"\n💾 Đã lưu model vào: {path}")
    
    def visualize_results(self, X_test, y_test, save_path: str = 'data/model_performance.png'):
        """
        Visualize kết quả dự đoán
        
        Args:
            X_test: test features
            y_test: test labels
            save_path: đường dẫn lưu hình
        """
        if self.best_model is None:
            print("⚠️  Chưa có model để visualize")
            return
        
        print(f"\n📊 Đang tạo visualization...")
        
        # Predict
        y_pred = self.best_model.predict(X_test)
        
        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Actual vs Predicted
        axes[0].scatter(y_test, y_pred, alpha=0.5, s=30)
        axes[0].plot([0, 100], [0, 100], 'r--', lw=2)
        axes[0].set_xlabel('Điểm thực tế', fontsize=12)
        axes[0].set_ylabel('Điểm dự đoán', fontsize=12)
        axes[0].set_title(f'Actual vs Predicted - {self.best_model_name}', fontsize=14)
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Residuals
        residuals = y_test - y_pred
        axes[1].scatter(y_pred, residuals, alpha=0.5, s=30)
        axes[1].axhline(y=0, color='r', linestyle='--', lw=2)
        axes[1].set_xlabel('Điểm dự đoán', fontsize=12)
        axes[1].set_ylabel('Residuals', fontsize=12)
        axes[1].set_title('Residual Plot', fontsize=14)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Lưu hình
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        print(f"   ✓ Đã lưu visualization: {save_path}")
        
        plt.close()


def main():
    """Main function để chạy training"""
    
    print("="*80)
    print("  🤖 HỆ THỐNG HUẤN LUYỆN MÔ HÌNH CHẤM ĐIỂM CV")
    print("="*80)
    
    # Khởi tạo trainer
    trainer = CVModelTrainer()
    
    # 1. Tạo hoặc load dataset
    dataset_path = 'data/synthetic_cv_dataset.csv'
    
    if os.path.exists(dataset_path):
        print(f"\n📂 Load dataset từ {dataset_path}")
        df = pd.read_csv(dataset_path)
    else:
        print("\n📝 Chưa có dataset, tạo synthetic dataset mới...")
        df = trainer.generate_dataset(samples_per_job=100)
        
        # Lưu dataset
        os.makedirs('data', exist_ok=True)
        df.to_csv(dataset_path, index=False)
        print(f"💾 Đã lưu dataset vào {dataset_path}")
    
    # 2. Chuẩn bị features
    X, y = trainer.prepare_features(df)
    
    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )
    
    print(f"\n📊 Kích thước dữ liệu:")
    print(f"   Training: {X_train.shape[0]} samples")
    print(f"   Testing: {X_test.shape[0]} samples")
    
    # 4. Huấn luyện models
    results_df = trainer.train_models(X_train, y_train, X_test, y_test)
    
    # 5. Visualize
    trainer.visualize_results(X_test, y_test)
    
    # 6. Lưu model
    trainer.save_model('cv_analyzer/models/cv_scorer_model.pkl')
    
    print("\n" + "="*80)
    print("  ✅ HOÀN THÀNH HUẤN LUYỆN MÔ HÌNH")
    print("="*80)
    print("\n💡 Để sử dụng model trong app:")
    print("   1. Model đã được lưu tại: cv_analyzer/models/cv_scorer_model.pkl")
    print("   2. App sẽ tự động load model khi khởi động")
    print("   3. Nếu không có model, app vẫn chạy bằng phương pháp rule-based")
    print("\n🚀 Bây giờ bạn có thể chạy: streamlit run cv_analyzer/app.py\n")


if __name__ == "__main__":
    main()
