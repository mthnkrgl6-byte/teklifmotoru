# AI Plumbing Product Detection Engine

AI-powered quotation system for plumbing materials companies. The app ingests customer files (Excel, PDF, images/screenshots), extracts text with OCR when needed, detects products with typo correction + AI assistance, matches them against a PostgreSQL product catalog, and generates/exportable quotations.

## Features
- Upload `.xlsx`, `.pdf`, `.jpg`, `.jpeg`, `.png` files
- OCR for images and scanned PDFs (Tesseract)
- Text extraction from Excel/PDF/image files
- AI product detection (OpenAI API) with heuristic fallback
- Typo correction examples: `pvh dirsek -> pvc dirsek`, `ppr boru -> pprc boru`
- Product matching with fuzzy logic + diameter scoring
- Quotation generation with subtotal, discount, VAT (20%), grand total
- Export quotation to Excel and PDF
- Dashboard with tabs: teklif analizi, güncel fiyat listesi yükleme, teklif seçenekleri
- React dashboard for upload, detection results, quotation table, exports

## Project Structure
```
/backend
  /app
    /api       # FastAPI routes
    /core      # settings
    /db        # SQLAlchemy setup
    /models    # Product model
    /schemas   # API schemas
    /services  # extraction, detection, matching, export
  /scripts/seed_products.sql
  requirements.txt
/frontend
  /src         # React app
/docker-compose.yml
```

## Quick Start (Docker)
1. Optionally set `OPENAI_API_KEY`:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```
2. Run stack:
   ```bash
   docker compose up --build
   ```
3. Open:
   - Frontend: http://localhost:5173
   - Backend docs: http://localhost:8000/docs

## Manual Setup
### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### PostgreSQL Seed
Run `backend/scripts/seed_products.sql` in your PostgreSQL database.

## API Endpoints
- `GET /api/health`
- `POST /api/analyze` (`multipart/form-data` with `file`, optional `discount`, `vat_rate`, `include_vat`)
- `GET /api/products`
- `POST /api/products/upload-pricelist` (xlsx/csv with columns: product_code, product_name, diameter, unit, price)
- `POST /api/export/xlsx`
- `POST /api/export/pdf`

## Notes for Production
- Place backend behind reverse proxy (Nginx/Traefik)
- Secure CORS and auth (JWT/API keys)
- Move exports to object storage
- Add async workers (Celery/RQ) for large OCR jobs
- Add observability and rate limits
