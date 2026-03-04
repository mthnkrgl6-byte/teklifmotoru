import { useState } from 'react';
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api' });

export default function App() {
  const [file, setFile] = useState(null);
  const [discount, setDiscount] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('discount', discount);
    const response = await api.post('/analyze', formData);
    setResult(response.data);
    setLoading(false);
  };

  const exportQuote = async (format) => {
    if (!result) return;
    const response = await api.post(`/export/${format}`, result, { responseType: 'blob' });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quotation.${format}`;
    a.click();
  };

  return (
    <div className="container">
      <h1>AI Plumbing Product Detection Engine</h1>
      <div className="card">
        <input type="file" accept=".xlsx,.pdf,.jpg,.jpeg,.png" onChange={(e) => setFile(e.target.files[0])} />
        <input type="number" value={discount} min={0} step={0.01} onChange={(e) => setDiscount(Number(e.target.value))} placeholder="Discount" />
        <button onClick={analyze} disabled={loading}>{loading ? 'Analyzing...' : 'Analyze'}</button>
      </div>
      {result && (
        <>
          <div className="card">
            <h2>Detected Items</h2>
            <ul>
              {result.detected_items.map((item, idx) => (
                <li key={idx}>{item.product_name} {item.diameter ? `(${item.diameter})` : ''} - Qty: {item.quantity}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h2>Quotation Table</h2>
            <table>
              <thead><tr><th>Product</th><th>Code</th><th>Qty</th><th>Unit</th><th>Total</th></tr></thead>
              <tbody>
                {result.quotation_rows.map((row, idx) => (
                  <tr key={idx}><td>{row.product_name}</td><td>{row.product_code}</td><td>{row.quantity}</td><td>{row.unit_price}</td><td>{row.total_price}</td></tr>
                ))}
              </tbody>
            </table>
            <p>Subtotal: {result.summary.subtotal}</p>
            <p>Discount: {result.summary.discount}</p>
            <p>VAT: {result.summary.vat_amount}</p>
            <p>Grand Total: {result.summary.grand_total}</p>
            <button onClick={() => exportQuote('xlsx')}>Export Excel</button>
            <button onClick={() => exportQuote('pdf')}>Export PDF</button>
          </div>
        </>
      )}
    </div>
  );
}
