"""
Module quản lý từ điển kỹ năng IT và mô tả vị trí thực tập
"""

from typing import Dict, List

# Từ điển kỹ năng IT phân theo nhóm (hơn 150 kỹ năng)
SKILLS_DATABASE: Dict[str, List[str]] = {
    "Ngôn ngữ lập trình": [
        "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "PHP",
        "Ruby", "Go", "Golang", "Rust", "Swift", "Kotlin", "Dart", "Scala",
        "R", "MATLAB", "Perl", "Shell", "Bash", "PowerShell", "Objective-C",
        "Visual Basic", "Assembly", "Solidity", "Elixir", "Haskell", "Julia"
    ],
    
    "Web Frontend": [
        "HTML", "HTML5", "CSS", "CSS3", "SASS", "SCSS", "LESS", "Tailwind CSS",
        "Bootstrap", "Material UI", "Ant Design", "Chakra UI", "Bulma",
        "React", "ReactJS", "React Native", "Redux", "MobX", "Context API",
        "Vue", "Vue.js", "Vuex", "Pinia", "Nuxt.js",
        "Angular", "AngularJS", "RxJS", "NgRx",
        "jQuery", "Next.js", "Gatsby", "Svelte", "SvelteKit",
        "Webpack", "Vite", "Parcel", "Rollup", "Babel",
        "Responsive Design", "Mobile First", "Progressive Web App", "PWA"
    ],
    
    "Web Backend": [
        "Node.js", "Express", "Express.js", "NestJS", "Fastify", "Koa",
        "Django", "Flask", "FastAPI", "Pyramid", "Tornado",
        "Spring", "Spring Boot", "Spring MVC", "Hibernate",
        "Laravel", "Symfony", "CodeIgniter", "CakePHP",
        "Ruby on Rails", "ASP.NET", ".NET Core", "ASP.NET MVC",
        "GraphQL", "RESTful API", "REST API", "SOAP", "gRPC", "WebSocket",
        "Microservices", "Serverless", "API Gateway", "OAuth", "JWT"
    ],
    
    "Mobile Development": [
        "Android", "iOS", "React Native", "Flutter", "Xamarin", "Ionic",
        "Kotlin", "Swift", "SwiftUI", "Jetpack Compose",
        "Android Studio", "Xcode", "Cordova", "PhoneGap",
        "Mobile UI/UX", "Material Design", "Human Interface Guidelines"
    ],
    
    "Database": [
        "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MariaDB", "SQLite",
        "MongoDB", "Cassandra", "CouchDB", "Redis", "Memcached",
        "Elasticsearch", "Neo4j", "DynamoDB", "Firebase", "Firestore",
        "SQL", "NoSQL", "Database Design", "Query Optimization",
        "ORMs", "SQLAlchemy", "Sequelize", "Prisma", "TypeORM"
    ],
    
    "AI & Machine Learning": [
        "Machine Learning", "Deep Learning", "Neural Networks", "CNN", "RNN", "LSTM",
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM",
        "Computer Vision", "OpenCV", "YOLO", "Object Detection",
        "Natural Language Processing", "NLP", "NLTK", "spaCy", "Transformers",
        "Large Language Models", "LLM", "GPT", "BERT", "Hugging Face",
        "Data Science", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
        "Statistical Analysis", "A/B Testing", "Feature Engineering",
        "Model Deployment", "MLOps", "MLflow", "Kubeflow"
    ],
    
    "Data Engineering & Analytics": [
        "ETL", "Data Pipeline", "Data Warehouse", "Data Lake",
        "Apache Spark", "PySpark", "Hadoop", "Hive", "Kafka", "Airflow",
        "Power BI", "Tableau", "Looker", "Google Data Studio", "Metabase",
        "Google BigQuery", "Amazon Redshift", "Snowflake", "Databricks",
        "Data Modeling", "Data Mining", "Business Intelligence", "BI"
    ],
    
    "DevOps & Cloud": [
        "Docker", "Kubernetes", "K8s", "Jenkins", "GitLab CI", "GitHub Actions",
        "CircleCI", "Travis CI", "Terraform", "Ansible", "Puppet", "Chef",
        "AWS", "Amazon Web Services", "EC2", "S3", "Lambda", "RDS", "CloudWatch",
        "Azure", "Microsoft Azure", "Azure DevOps", "Azure Functions",
        "Google Cloud", "GCP", "Google Cloud Platform", "App Engine", "Cloud Run",
        "CI/CD", "Continuous Integration", "Continuous Deployment",
        "Linux", "Ubuntu", "CentOS", "Unix", "Shell Scripting",
        "Nginx", "Apache", "Load Balancing", "Monitoring", "Prometheus", "Grafana"
    ],
    
    "Testing & QA": [
        "Unit Testing", "Integration Testing", "E2E Testing", "Automation Testing",
        "Jest", "Mocha", "Chai", "Jasmine", "Pytest", "JUnit", "TestNG",
        "Selenium", "Cypress", "Playwright", "Puppeteer", "Appium",
        "Postman", "JMeter", "LoadRunner", "Performance Testing",
        "Manual Testing", "Test Cases", "Bug Tracking", "Quality Assurance"
    ],
    
    "UI/UX Design": [
        "Figma", "Adobe XD", "Sketch", "InVision", "Zeplin", "Adobe Photoshop",
        "Adobe Illustrator", "Wireframing", "Prototyping", "User Research",
        "User Testing", "Usability Testing", "Information Architecture",
        "Interaction Design", "Visual Design", "Design Systems", "Accessibility"
    ],
    
    "Security": [
        "Cybersecurity", "Information Security", "Network Security",
        "Penetration Testing", "Ethical Hacking", "Vulnerability Assessment",
        "OWASP", "SQL Injection", "XSS", "CSRF", "Security Audit",
        "Cryptography", "SSL/TLS", "Encryption", "Firewall", "IDS/IPS",
        "SIEM", "Security Compliance", "ISO 27001", "GDPR"
    ],
    
    "Version Control & Tools": [
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
        "JIRA", "Confluence", "Trello", "Asana", "Slack", "Teams",
        "VS Code", "Visual Studio", "IntelliJ IDEA", "PyCharm", "Eclipse"
    ],
    
    "Soft Skills & Methods": [
        "Agile", "Scrum", "Kanban", "Waterfall", "Lean",
        "Problem Solving", "Teamwork", "Communication", "Leadership",
        "Time Management", "Critical Thinking", "Analytical Skills",
        "Presentation Skills", "Technical Writing", "Documentation"
    ]
}

# Tổng hợp tất cả kỹ năng thành một danh sách phẳng
ALL_SKILLS: List[str] = []
for category_skills in SKILLS_DATABASE.values():
    ALL_SKILLS.extend(category_skills)

# Mô tả chi tiết các vị trí thực tập
JOB_DESCRIPTIONS: Dict[str, Dict[str, any]] = {
    "Backend Developer": {
        "description": "Phát triển và duy trì các hệ thống server-side, API, và database cho ứng dụng web",
        "required_skills": [
            "Python", "Java", "Node.js", "Django", "Flask", "FastAPI", "Spring Boot",
            "RESTful API", "GraphQL", "SQL", "PostgreSQL", "MySQL", "MongoDB",
            "Git", "Docker", "Microservices", "API Design", "Database Design"
        ],
        "preferred_skills": [
            "Redis", "Kafka", "RabbitMQ", "AWS", "Kubernetes", "CI/CD",
            "Unit Testing", "Design Patterns", "System Design"
        ],
        "responsibilities": [
            "Thiết kế và phát triển RESTful API",
            "Tối ưu hóa database và query performance",
            "Xây dựng và duy trì microservices",
            "Viết unit test và integration test",
            "Làm việc với team frontend để tích hợp API"
        ]
    },
    
    "Frontend Developer": {
        "description": "Xây dựng giao diện người dùng đẹp mắt và tương tác tốt cho ứng dụng web",
        "required_skills": [
            "HTML", "CSS", "JavaScript", "TypeScript", "React", "Vue.js", "Angular",
            "Responsive Design", "Git", "RESTful API", "State Management",
            "Bootstrap", "Tailwind CSS", "Webpack", "npm"
        ],
        "preferred_skills": [
            "Next.js", "Redux", "Vuex", "SASS", "Testing Library", "Jest",
            "UI/UX Design", "Performance Optimization", "PWA", "Accessibility"
        ],
        "responsibilities": [
            "Phát triển UI components tái sử dụng",
            "Tối ưu performance và trải nghiệm người dùng",
            "Tích hợp API với backend",
            "Đảm bảo responsive trên mọi thiết bị",
            "Code review và maintain code quality"
        ]
    },
    
    "Fullstack Developer": {
        "description": "Phát triển cả frontend lẫn backend, có khả năng xây dựng ứng dụng web hoàn chỉnh",
        "required_skills": [
            "JavaScript", "TypeScript", "React", "Node.js", "Express",
            "SQL", "MongoDB", "RESTful API", "Git", "HTML", "CSS",
            "Database Design", "API Design", "Authentication"
        ],
        "preferred_skills": [
            "Next.js", "NestJS", "Docker", "AWS", "Redis", "GraphQL",
            "Testing", "CI/CD", "System Design", "Microservices"
        ],
        "responsibilities": [
            "Phát triển full-stack web applications",
            "Thiết kế database schema và API",
            "Implement authentication và authorization",
            "Deploy và maintain applications",
            "Collaborate với designers và stakeholders"
        ]
    },
    
    "Mobile Developer": {
        "description": "Phát triển ứng dụng di động cho Android và/hoặc iOS",
        "required_skills": [
            "React Native", "Flutter", "Android", "iOS", "Kotlin", "Swift",
            "Mobile UI/UX", "RESTful API", "Git", "State Management",
            "App Store", "Google Play", "Mobile Design Patterns"
        ],
        "preferred_skills": [
            "Firebase", "Push Notifications", "In-App Purchase", "Maps API",
            "Camera API", "Offline Storage", "Performance Optimization",
            "App Analytics", "CI/CD for Mobile"
        ],
        "responsibilities": [
            "Phát triển mobile app cho iOS và Android",
            "Tối ưu performance và battery usage",
            "Implement mobile-specific features",
            "Testing trên nhiều devices",
            "Submit app lên stores và maintain"
        ]
    },
    
    "Data Analyst / Data Engineer": {
        "description": "Thu thập, xử lý và phân tích dữ liệu để đưa ra insights có giá trị",
        "required_skills": [
            "Python", "SQL", "Pandas", "NumPy", "Data Analysis", "ETL",
            "Excel", "Statistics", "Data Visualization", "Power BI", "Tableau",
            "Database Design", "Data Modeling", "Git"
        ],
        "preferred_skills": [
            "Apache Spark", "Airflow", "BigQuery", "Snowflake", "dbt",
            "AWS", "Machine Learning", "Scikit-learn", "A/B Testing",
            "Data Warehouse", "Data Pipeline"
        ],
        "responsibilities": [
            "Xây dựng và maintain data pipelines",
            "Phân tích dữ liệu và tạo reports",
            "Thiết kế dashboards và visualizations",
            "Optimize queries và database performance",
            "Collaborate với stakeholders để hiểu requirements"
        ]
    },
    
    "AI / Machine Learning Engineer": {
        "description": "Phát triển và deploy các mô hình Machine Learning và AI",
        "required_skills": [
            "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Scikit-learn", "Pandas", "NumPy", "Statistics", "Linear Algebra",
            "Data Preprocessing", "Model Evaluation", "Git"
        ],
        "preferred_skills": [
            "NLP", "Computer Vision", "MLOps", "Docker", "Kubernetes",
            "AWS SageMaker", "Feature Engineering", "Hyperparameter Tuning",
            "Model Deployment", "A/B Testing", "Research Papers"
        ],
        "responsibilities": [
            "Phát triển và train ML models",
            "Feature engineering và data preprocessing",
            "Evaluate và optimize model performance",
            "Deploy models to production",
            "Research và implement state-of-the-art techniques"
        ]
    },
    
    "DevOps Engineer": {
        "description": "Quản lý infrastructure, automation, và CI/CD pipelines",
        "required_skills": [
            "Linux", "Docker", "Kubernetes", "Git", "CI/CD", "Jenkins",
            "Shell Scripting", "AWS", "Terraform", "Ansible", "Monitoring",
            "Networking", "Security Best Practices"
        ],
        "preferred_skills": [
            "GitLab CI", "GitHub Actions", "Prometheus", "Grafana", "ELK Stack",
            "Helm", "ArgoCD", "Infrastructure as Code", "Cloud Architecture",
            "Cost Optimization", "High Availability"
        ],
        "responsibilities": [
            "Thiết lập và maintain CI/CD pipelines",
            "Manage cloud infrastructure",
            "Automate deployment processes",
            "Monitor system health và performance",
            "Ensure security và compliance"
        ]
    },
    
    "QA / Software Tester": {
        "description": "Đảm bảo chất lượng phần mềm thông qua testing và quality assurance",
        "required_skills": [
            "Manual Testing", "Test Cases", "Bug Tracking", "JIRA", "Git",
            "Automation Testing", "Selenium", "API Testing", "Postman",
            "SQL", "Agile", "Test Planning", "Quality Assurance"
        ],
        "preferred_skills": [
            "Cypress", "Playwright", "Jest", "Performance Testing", "JMeter",
            "CI/CD", "Python", "JavaScript", "Mobile Testing", "Security Testing"
        ],
        "responsibilities": [
            "Viết và execute test cases",
            "Tìm và report bugs chi tiết",
            "Automation testing cho regression",
            "API testing và validation",
            "Collaborate với developers để fix issues"
        ]
    },
    
    "UI/UX Designer": {
        "description": "Thiết kế giao diện và trải nghiệm người dùng cho sản phẩm digital",
        "required_skills": [
            "Figma", "Adobe XD", "Sketch", "UI Design", "UX Design",
            "Wireframing", "Prototyping", "User Research", "Usability Testing",
            "Design Systems", "Visual Design", "Interaction Design"
        ],
        "preferred_skills": [
            "HTML", "CSS", "JavaScript", "After Effects", "Illustration",
            "Motion Design", "Accessibility", "Design Thinking",
            "User Journey Mapping", "A/B Testing"
        ],
        "responsibilities": [
            "Thiết kế UI mockups và prototypes",
            "Conduct user research và testing",
            "Tạo design systems và style guides",
            "Collaborate với developers",
            "Iterate designs based on feedback"
        ]
    },
    
    "Cybersecurity / An toàn thông tin": {
        "description": "Bảo vệ hệ thống và dữ liệu khỏi các mối đe dọa an ninh mạng",
        "required_skills": [
            "Network Security", "Cybersecurity", "Penetration Testing",
            "Vulnerability Assessment", "Security Audit", "Firewall", "IDS/IPS",
            "OWASP", "Cryptography", "Linux", "Security Tools", "Risk Assessment"
        ],
        "preferred_skills": [
            "Ethical Hacking", "SIEM", "Incident Response", "Malware Analysis",
            "Cloud Security", "Compliance", "Python", "Security Automation",
            "Threat Intelligence", "Forensics"
        ],
        "responsibilities": [
            "Phát hiện và xử lý security vulnerabilities",
            "Thực hiện penetration testing",
            "Monitor security events",
            "Implement security best practices",
            "Security awareness training"
        ]
    }
}


def get_all_skills() -> List[str]:
    """Lấy danh sách tất cả kỹ năng"""
    return ALL_SKILLS


def get_skills_by_category(category: str) -> List[str]:
    """Lấy kỹ năng theo nhóm"""
    return SKILLS_DATABASE.get(category, [])


def get_job_info(job_title: str) -> Dict:
    """Lấy thông tin chi tiết về vị trí công việc"""
    return JOB_DESCRIPTIONS.get(job_title, {})


def get_all_job_titles() -> List[str]:
    """Lấy danh sách tất cả vị trí công việc"""
    return list(JOB_DESCRIPTIONS.keys())


def get_required_skills_for_job(job_title: str) -> List[str]:
    """Lấy danh sách kỹ năng bắt buộc cho vị trí"""
    job_info = get_job_info(job_title)
    return job_info.get("required_skills", [])


def get_preferred_skills_for_job(job_title: str) -> List[str]:
    """Lấy danh sách kỹ năng ưu tiên cho vị trí"""
    job_info = get_job_info(job_title)
    return job_info.get("preferred_skills", [])
