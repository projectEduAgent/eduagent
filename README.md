# EduAgent — RAG Pipeline & Vektör Veritabanı

Bu belge, EduAgent projesinin **RAG Pipeline & Vektör Veritabanı** bileşenini açıklamaktadır.

---

## Genel Bakış

Öğrenciler bir PDF yükler, sistem bu belgeyi parçalara ayırır, vektöre dönüştürür ve ChromaDB'de saklar. Öğrenci soru sorduğunda, en alakalı parçalar bulunur ve yerel bir LLM (Ollama) bu parçalara dayanarak cevap üretir.

```
PDF Yükleme → Parçalara Ayırma → Embedding → ChromaDB
                                                  ↓
Öğrenci Sorusu → Benzerlik Araması → İlgili Parçalar → Ollama LLM → Cevap
```

---

## Dosya Yapısı

```
eduagent/
├── rag/
│   ├── pipeline.py     ← Diğer agent'ların kullandığı tek giriş noktası
│   ├── loader.py       ← PDF okuma ve parçalara ayırma
│   ├── embedder.py     ← Embedding oluşturma ve ChromaDB'ye kaydetme
│   └── retriever.py    ← ChromaDB'den benzer parçaları getirme
├── agents/
│   └── answer_agent.py ← Ollama LLM ile cevap üretme
├── app.py              ← Streamlit web arayüzü
├── Dockerfile          ← Docker image tanımı
├── docker-compose.yml  ← App + Ollama servislerini ayağa kaldırır
└── requirements.txt    ← Python bağımlılıkları
```

---

## Teknoloji Yığını

| Bileşen | Teknoloji |
|---|---|
| PDF Okuma | LangChain `PyPDFLoader` |
| Metin Parçalama | LangChain `RecursiveCharacterTextSplitter` |
| Embedding Modeli | `all-MiniLM-L6-v2` (HuggingFace, yerel) |
| Vektör Veritabanı | ChromaDB (yerel dosya tabanlı) |
| LLM | Ollama `qwen3.5:9b` (yerel) |
| Web Arayüzü | Streamlit |
| Konteyner | Docker + Docker Compose |

> İnternet bağlantısı veya API anahtarı gerekmez. Her şey yerel çalışır.

---

## Diğer Agent'lar İçin Kullanım

Monitor, Evaluator veya başka bir agent ekleyecekseniz sadece şu iki fonksiyonu import edin:

```python
from rag.pipeline import load_and_index_pdf, search

# PDF'i indeksle (bir kez yapılır)
load_and_index_pdf("belge.pdf")

# Soru için en alakalı 3 parçayı getir
chunks = search("Q-Learning nedir?")
# chunks → ["Q-Learning bir pekiştirmeli öğrenme...", ...]
```

`loader.py`, `embedder.py` veya `retriever.py` dosyalarını **doğrudan import etmeyin** — her şey `pipeline.py` üzerinden geçmeli.

---

## Kurulum ve Çalıştırma

### Docker ile (Önerilen)

```bash
# 1. Servisleri ayağa kaldır
docker compose up --build

# 2. İlk çalıştırmada modeli indir (bir kez yapılır)
docker exec -it eduagent-ollama ollama pull qwen3.5:9b

# 3. Tarayıcıda aç
# http://localhost:8501
```

### Yerel Geliştirme (Docker olmadan)

```bash
# 1. Sanal ortam oluştur
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Ollama'yı başlat ve modeli indir
ollama serve
ollama pull qwen3.5:9b

# 4. Uygulamayı çalıştır
streamlit run app.py
```

---

## Nasıl Kullanılır

1. Tarayıcıda `http://localhost:8501` adresini aç
2. **"Choose a PDF file"** ile bir PDF yükle
3. **"Process PDF"** butonuna tıkla — PDF parçalanır ve ChromaDB'ye kaydedilir
4. Soru kutusuna soruyu yaz
5. **"Search"** butonuna tıkla — cevap ekrana gelir

---

## RAG Pipeline Nasıl Çalışır?

### 1. İndeksleme (PDF Yüklenince)

```
PDF
 └─► PyPDFLoader        → sayfa sayfa okur
      └─► TextSplitter  → 500 karakterlik parçalara böler (50 karakter örtüşme)
           └─► HuggingFaceEmbeddings  → her parçayı vektöre dönüştürür
                └─► ChromaDB         → vektörleri diske kaydeder
```

### 2. Arama (Soru Sorulunca)

```
Soru
 └─► HuggingFaceEmbeddings  → soruyu vektöre dönüştürür
      └─► ChromaDB           → en benzer 3 parçayı bulur
           └─► Ollama LLM    → parçalar + soru → cevap üretir
```

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama sunucu adresi. Docker'da otomatik `http://ollama:11434` olarak ayarlanır. |

---

## Bağımlılıklar

```
streamlit
langchain
langchain-community
langchain-huggingface
langchain-chroma
langchain-ollama
chromadb
sentence-transformers
pypdf
python-dotenv
```
