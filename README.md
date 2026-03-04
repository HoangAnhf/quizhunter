# QuizHunter

**Ung dung Tro ly AI Tim kiem, Quan ly va Phan tich De thi thong minh**

QuizHunter la ung dung web Streamlit da trang (multi-page) giup hoc sinh va giao vien tim kiem, tao, quan ly va luyen tap de thi. Ung dung ket hop tri tue nhan tao (AI), tim kiem ngu nghia (semantic search), va chuong trinh giao duc Viet Nam tu lop 1 den lop 12.

## Tinh nang chinh

### Tim kiem thong minh
- Tim kiem ngu nghia bang **Sentence-Transformers + FAISS** — nhap "toan 9" se tu dong tim de Toan lop 9
- Tim kiem bang **giong noi** (Deepgram Speech-to-Text, ho tro tieng Viet)
- Tim kiem tren web (OpenTDB, crawl tu website)
- Hybrid search: ket hop semantic + keyword fallback

### Quan ly Kho de
- **170+ de thi** voi **1,200+ cau hoi** trong 12 mon hoc
- Ma de tu dong (VD: `TOAN-8-CB-001`) de tra cuu nhanh
- Loc theo mon hoc, muc do, lop
- Xem chi tiet, xuat PDF/DOCX/TXT, in de thi
- Xoa de, phan trang

### Tao de bang AI
- Tao de tu dong bang **Groq (Llama 3.3 70B)** hoac **Google Gemini**
- Chon mon, lop, so cau, muc do, chu de
- Ho tro trac nghiem, tu luan, bai tap
- Giai thich dap an bang AI
- Luu vao kho de hoac lam de ngay

### Lam de thi (Practice Mode)
- Chon de tu kho → lam bai trac nghiem tuong tac
- **Dong ho dem nguoc** tu dong phat hien tu ten de (VD: "15 p" → 15 phut)
- Canh bao khi con duoi 5 phut, tu dong nop khi het gio
- **Dialog xac nhan** nop bai voi 2 lua chon Co/Khong
- Ket qua chi tiet: dung/sai tung cau, dap an dung
- Robot cam xuc theo ket qua (tu 🤖😢 den 🤖✨)
- Lam lai de hoac chon de khac

### Tien trinh hoc tap
- Tong quan: so lan lam, diem trung binh (thang 10), tong thoi gian
- **Bieu do cot** xu huong diem theo thoi gian voi thanh keo chon khoang
- Ket qua theo tung mon hoc
- Loc theo mon hoc (multiselect)
- Lich su lam de chi tiet

### Upload va Crawl
- Upload file **PDF/DOCX/TXT** → AI tu dong trich xuat cau hoi
- **Web crawler** voi ho tro LaTeX → Unicode, loc spam
- Luu truc tiep vao kho de MySQL

### Dashboard Thong ke
- Tong quan: so de, so cau hoi, so mon
- Bieu do theo mon, muc do, lop, loai cau hoi
- Top 10 de nhieu cau nhat
- Thong ke nguon de thi

## Cong nghe su dung

| Thanh phan | Cong nghe |
|------------|-----------|
| Frontend | Streamlit, Custom CSS, Altair Charts |
| AI/ML | Sentence-Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Vector Search | FAISS (Facebook AI Similarity Search) |
| LLM | Groq (Llama 3.3 70B), Google Gemini Flash |
| Database | MySQL 8.0, Connection Pooling |
| Speech-to-Text | Deepgram Nova-2 (tieng Viet) |
| Export | fpdf2 (PDF), python-docx (DOCX) |
| Web Scraping | BeautifulSoup4, Requests |
| Timer | streamlit-autorefresh |

## Cau truc du an

```
quizhunter/
├── backend/
│   ├── core/
│   │   ├── search_engine.py        # Semantic search + query parser
│   │   ├── classifier.py           # Phan loai cau hoi
│   │   └── text_processor.py       # Xu ly van ban
│   ├── database/
│   │   ├── mysql_store.py          # MySQL CRUD (chinh)
│   │   ├── vector_store.py         # FAISS index
│   │   └── exam_store.py           # JSON storage (cu)
│   ├── extractors/
│   │   ├── pdf_extractor.py        # Trich xuat PDF
│   │   ├── docx_extractor.py       # Trich xuat DOCX
│   │   └── txt_extractor.py        # Trich xuat TXT
│   ├── models/
│   │   ├── embedding_model.py      # Sentence-Transformers wrapper
│   │   └── classification_model.py # ML classification
│   ├── schemas/
│   │   └── exam.py                 # Exam, Question, SearchResult dataclass
│   └── services/
│       ├── groq_service.py         # Groq AI API
│       ├── gemini_service.py       # Google Gemini API
│       ├── ai_explain.py           # Giai thich dap an
│       ├── curriculum.py           # Chuong trinh giao duc VN
│       ├── exam_export.py          # Xuat PDF/DOCX
│       ├── web_search.py           # Tim kiem web
│       ├── web_crawler.py          # Crawl de thi
│       ├── question_bank.py        # Ngan hang cau hoi JSON
│       ├── deepgram_service.py     # Speech-to-text
│       └── translator.py           # Dich ngon ngu
├── frontend/
│   ├── app.py                      # Trang chu
│   ├── pages/
│   │   ├── 1_🔍_Tim_kiem.py        # Tim kiem de thi
│   │   ├── 2_📤_Upload.py          # Upload file
│   │   ├── 3_📚_Kho_de.py          # Kho de thi
│   │   ├── 4_ℹ️_Gioi_thieu.py      # Gioi thieu
│   │   ├── 5_🌐_Crawl_de.py        # Crawl de tu web
│   │   ├── 6_🤖_Tao_de.py          # Tao de bang AI
│   │   ├── 7_📊_Dashboard.py       # Thong ke
│   │   ├── 8_📝_Lam_de.py          # Lam de thi
│   │   └── 9_📈_Tien_trinh.py      # Tien trinh hoc tap
│   ├── components/
│   │   ├── exam_card.py            # Card hien thi de thi
│   │   ├── search_bar.py           # Thanh tim kiem
│   │   └── sidebar.py              # Bo loc sidebar
│   ├── static/
│   │   └── style.css               # Custom CSS
│   └── utils/
│       └── ui_helpers.py           # Tien ich UI
├── data/
│   ├── question_bank/              # 12 file JSON (1,242 cau hoi)
│   ├── exam_database.json          # Kho de JSON (legacy)
│   ├── faiss_index/                # FAISS vector index
│   └── sample_exams/               # De thi mau
├── config.py                       # Cau hinh trung tam
├── requirements.txt                # Thu vien Python
├── setup.py                        # Cai dat package
└── README.md
```

## Cai dat

### Yeu cau
- Python 3.10+
- MySQL 8.0+
- Tai khoan API: Groq (mien phi), Google Gemini (mien phi), Deepgram (tuy chon)

### Buoc 1: Clone va cai dat

```bash
git clone https://github.com/HoangAnhf/quizhunter.git
cd quizhunter
pip install -e . --config-settings editable_mode=compat
```

### Buoc 2: Cau hinh MySQL

Tao database va user:

```sql
CREATE DATABASE quizhunter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'quizhunter'@'localhost' IDENTIFIED BY '1234567';
GRANT ALL PRIVILEGES ON quizhunter.* TO 'quizhunter'@'localhost';
```

Tao bang:

```sql
CREATE TABLE exams (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    subject VARCHAR(100),
    difficulty VARCHAR(50),
    source_file VARCHAR(500),
    grade INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    exam_code VARCHAR(30) DEFAULT NULL,
    UNIQUE INDEX idx_exam_code (exam_code)
);

CREATE TABLE questions (
    id VARCHAR(36) PRIMARY KEY,
    content TEXT NOT NULL,
    options JSON,
    answer TEXT,
    question_type VARCHAR(50),
    subject VARCHAR(100),
    grade INT,
    difficulty VARCHAR(50),
    topic VARCHAR(200),
    solution TEXT,
    comment TEXT,
    column_a JSON,
    column_b JSON,
    FULLTEXT INDEX idx_content (content)
);

CREATE TABLE exam_questions (
    exam_id VARCHAR(36),
    question_id VARCHAR(36),
    position INT,
    PRIMARY KEY (exam_id, question_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    query VARCHAR(500),
    results_count INT DEFAULT 0,
    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quiz_sessions (
    id VARCHAR(36) PRIMARY KEY,
    exam_id VARCHAR(36) NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    score INT DEFAULT 0,
    total INT DEFAULT 0,
    time_spent_seconds INT DEFAULT 0,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE TABLE quiz_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(36) NOT NULL,
    user_answer TEXT,
    is_correct TINYINT(1) DEFAULT 0,
    answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES quiz_sessions(id) ON DELETE CASCADE
);
```

### Buoc 3: Cau hinh API keys

Chinh sua `config.py`:

```python
DEEPGRAM_API_KEY = "your_key"       # Tuy chon (cho voice search)
GEMINI_API_KEYS = ["key1", "key2"]  # Google Gemini
GROQ_API_KEYS = ["key1", "key2"]    # Groq (mien phi)
```

### Buoc 4: Chay ung dung

```bash
cd quizhunter
streamlit run frontend/app.py
```

Truy cap: http://localhost:8501

## Mon hoc ho tro

| Mon | Ma de | File JSON |
|-----|-------|-----------|
| Toan hoc | TOAN | toan.json |
| Vat ly | LY | vat_ly.json |
| Hoa hoc | HOA | hoa_hoc.json |
| Sinh hoc | SINH | sinh_hoc.json |
| Lich su | SU | lich_su.json |
| Dia ly | DIA | dia_ly.json |
| Tieng Anh | ANH | tieng_anh.json |
| Ngu van | VAN | ngu_van.json |
| Tin hoc | TIN | tin_hoc.json |
| GDCD | GDCD | gdcd.json |
| Cong nghe | CN | cong_nghe.json |
| The duc | TD | the_duc.json |

## Tac gia

- **Hoang Tuan Anh**
- Email: anh917015@gmail.com
- GitHub: [HoangAnhf](https://github.com/HoangAnhf/quizhunter.git)
