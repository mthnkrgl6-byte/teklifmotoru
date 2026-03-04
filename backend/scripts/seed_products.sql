CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    diameter VARCHAR(50),
    unit VARCHAR(20) DEFAULT 'adet',
    price NUMERIC(10,2) NOT NULL
);

INSERT INTO products (product_code, product_name, diameter, unit, price) VALUES
('KLD-PVC110D', 'PVC Dirsek', '110', 'adet', 120),
('KLD-PVC90D', 'PVC Dirsek', '90', 'adet', 95),
('KLD-PPRC32B', 'PPRC Boru', '32', 'metre', 35),
('KLD-PPRC20B', 'PPRC Boru', '20', 'metre', 22),
('KLD-KV20', 'Küresel Vana', '20', 'adet', 80),
('KLD-CK50', 'Çekvalf', '50', 'adet', 180)
ON CONFLICT (product_code) DO NOTHING;
