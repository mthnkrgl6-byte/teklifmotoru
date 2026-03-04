const DEFAULT_API_BASE = 'http://localhost:8000/api';

function getInitialApiBase() {
  const fromQuery = new URLSearchParams(window.location.search).get('api_base');
  if (fromQuery) return fromQuery.replace(/\/$/, '');

  const fromStorage = localStorage.getItem('api_base');
  if (fromStorage) return fromStorage.replace(/\/$/, '');

  if (window.location.protocol.startsWith('http')) {
    return `${window.location.origin}/api`;
  }

  return DEFAULT_API_BASE;
}

let API_BASE = getInitialApiBase();

const fileInput = document.getElementById('file');
const rawTextInput = document.getElementById('rawText');
const discountInput = document.getElementById('discount');
const vatRateInput = document.getElementById('vatRate');
const includeVatInput = document.getElementById('includeVat');
const apiBaseInput = document.getElementById('apiBase');
const saveApiBtn = document.getElementById('saveApiBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const excelBtn = document.getElementById('excelBtn');
const pdfBtn = document.getElementById('pdfBtn');
const statusText = document.getElementById('status');
const results = document.getElementById('results');
const detectedList = document.getElementById('detectedList');
const quoteBody = document.getElementById('quoteBody');
const summary = document.getElementById('summary');

const priceFileInput = document.getElementById('priceFile');
const uploadPriceBtn = document.getElementById('uploadPriceBtn');
const priceStatus = document.getElementById('priceStatus');
const refreshProductsBtn = document.getElementById('refreshProductsBtn');
const productsBody = document.getElementById('productsBody');

let analysisPayload = null;
apiBaseInput.value = API_BASE;

function setStatus(text) {
  statusText.textContent = text;
}

function setPriceStatus(text) {
  priceStatus.textContent = text;
}

function setApiBase(url) {
  API_BASE = url.replace(/\/$/, '');
  localStorage.setItem('api_base', API_BASE);
  apiBaseInput.value = API_BASE;
}

function setupTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabButtons.forEach((b) => b.classList.remove('active'));
      tabPanels.forEach((p) => p.classList.add('hidden'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.remove('hidden');
    });
  });
}

function renderProducts(products) {
  productsBody.innerHTML = '';
  products.forEach((p) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${p.product_code}</td>
      <td>${p.product_name}</td>
      <td>${p.diameter ?? '-'}</td>
      <td>${p.unit}</td>
      <td>${p.price}</td>
    `;
    productsBody.appendChild(tr);
  });
}

async function loadProducts() {
  const response = await fetch(`${API_BASE}/products`);
  if (!response.ok) throw new Error(`Ürün listesi alınamadı: ${response.status}`);
  const products = await response.json();
  renderProducts(products);
}

function renderResults(payload) {
  detectedList.innerHTML = '';
  quoteBody.innerHTML = '';

  payload.detected_items.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = `${item.product_name}${item.diameter ? ` (${item.diameter})` : ''} - Miktar: ${item.quantity}`;
    detectedList.appendChild(li);
  });

  payload.quotation_rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.product_name}</td>
      <td>${row.product_code}</td>
      <td>${row.diameter ?? '-'}</td>
      <td>${row.quantity}</td>
      <td>${row.unit_price}</td>
      <td>${row.total_price}</td>
    `;
    quoteBody.appendChild(tr);
  });

  summary.innerHTML = `
    <p>Ara Toplam: ${payload.summary.subtotal}</p>
    <p>İndirim: ${payload.summary.discount}</p>
    <p>KDV (${payload.summary.vat_rate * 100}%): ${payload.summary.vat_amount}</p>
    <p>Genel Toplam: ${payload.summary.grand_total}</p>
  `;

  results.classList.remove('hidden');
}

async function downloadQuote(format) {
  if (!analysisPayload) return;
  const response = await fetch(`${API_BASE}/export/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(analysisPayload),
  });
  if (!response.ok) throw new Error(`Export failed: ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `quotation.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function parseError(response) {
  try {
    const payload = await response.json();
    return payload.detail || JSON.stringify(payload);
  } catch {
    return `${response.status}`;
  }
}

function mapNetworkError(error) {
  if (String(error.message || '').includes('Failed to fetch')) {
    return `Backend'e ulaşılamadı. API URL'ini kontrol edin: ${API_BASE}`;
  }
  return error.message;
}

analyzeBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  const rawText = rawTextInput.value.trim();

  if (!file && !rawText) {
    setStatus('Dosya seçin veya metin girin.');
    return;
  }

  analyzeBtn.disabled = true;
  setStatus('Analiz ediliyor...');

  try {
    const formData = new FormData();
    if (file) formData.append('file', file);
    if (rawText) formData.append('raw_text', rawText);
    formData.append('discount', discountInput.value || '0');
    formData.append('vat_rate', vatRateInput.value || '0.2');
    formData.append('include_vat', includeVatInput.checked ? 'true' : 'false');

    const response = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData });
    if (!response.ok) throw new Error(await parseError(response));

    analysisPayload = await response.json();
    renderResults(analysisPayload);
    setStatus('Analiz tamamlandı.');
  } catch (error) {
    setStatus(`Hata: ${mapNetworkError(error)}`);
  } finally {
    analyzeBtn.disabled = false;
  }
});

uploadPriceBtn.addEventListener('click', async () => {
  const file = priceFileInput.files[0];
  if (!file) {
    setPriceStatus('Lütfen fiyat listesi dosyası seçin.');
    return;
  }

  uploadPriceBtn.disabled = true;
  setPriceStatus('Yükleniyor...');

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/products/upload-pricelist`, { method: 'POST', body: formData });
    if (!response.ok) throw new Error(await parseError(response));

    const payload = await response.json();
    setPriceStatus(`Tamamlandı. Yeni: ${payload.created}, Güncellenen: ${payload.updated}`);
    await loadProducts();
  } catch (error) {
    setPriceStatus(`Hata: ${mapNetworkError(error)}`);
  } finally {
    uploadPriceBtn.disabled = false;
  }
});

refreshProductsBtn.addEventListener('click', async () => {
  try {
    await loadProducts();
    setPriceStatus('Ürün listesi güncellendi.');
  } catch (error) {
    setPriceStatus(`Hata: ${mapNetworkError(error)}`);
  }
});

saveApiBtn.addEventListener('click', async () => {
  const value = apiBaseInput.value.trim();
  if (!value) return;
  setApiBase(value);
  setStatus(`API URL kaydedildi: ${API_BASE}`);
  try {
    await loadProducts();
  } catch {
    // no-op
  }
});

excelBtn.addEventListener('click', async () => {
  try {
    await downloadQuote('xlsx');
  } catch (error) {
    setStatus(`Excel indirilemedi: ${mapNetworkError(error)}`);
  }
});

pdfBtn.addEventListener('click', async () => {
  try {
    await downloadQuote('pdf');
  } catch (error) {
    setStatus(`PDF indirilemedi: ${mapNetworkError(error)}`);
  }
});

setupTabs();
loadProducts().catch(() => setPriceStatus(`Ürünler yüklenemedi. API URL: ${API_BASE}`));
