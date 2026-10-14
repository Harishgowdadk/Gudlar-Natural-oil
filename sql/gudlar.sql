-- ============================================================
-- GUDLAR (Sri Renuka Oil's) - Database Schema
-- Import this file in phpMyAdmin (XAMPP -> MySQL) before running the Flask app.
-- This is a product-catalog / stock-availability site only:
-- customer + admin accounts, cart, WhatsApp ordering, no payments.
-- ============================================================

CREATE DATABASE IF NOT EXISTS gudlar_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gudlar_db;

-- ---------- ADMINS ----------
CREATE TABLE IF NOT EXISTS admins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
-- NOTE: a default admin (admin / admin123) is auto-created the first time
-- the Flask app starts -- see db.py: ensure_default_admin()

-- ---------- USERS (customers) ----------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  phone VARCHAR(10) NOT NULL,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------- CATEGORIES ----------
CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL,
  slug VARCHAR(60) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO categories (name, slug) VALUES
  ('Coconut Oil', 'coconut-oil'),
  ('Groundnut Oil', 'groundnut-oil');

-- ---------- PRODUCTS ----------
CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  category_id INT NOT NULL,
  name VARCHAR(150) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  size_label VARCHAR(50) DEFAULT '1 Litre',
  image VARCHAR(255) DEFAULT NULL,
  stock INT DEFAULT 0,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

INSERT INTO products (category_id, name, description, price, size_label, stock) VALUES
  (1, "Sri Renuka Cold-Pressed Coconut Oil", "Pure, chemical-free coconut oil, wood cold-pressed the traditional way straight from our farm. No refining, no additives.", 320.00, "1 Litre", 40),
  (1, "Sri Renuka Cold-Pressed Coconut Oil", "Pure, chemical-free coconut oil, wood cold-pressed the traditional way straight from our farm. No refining, no additives.", 175.00, "500 ml", 60),
  (1, "Sri Renuka Cold-Pressed Coconut Oil", "Pure, chemical-free coconut oil, wood cold-pressed the traditional way straight from our farm. No refining, no additives.", 950.00, "5 Litre (Family Pack)", 0),
  (2, "Sri Renuka Wood-Pressed Groundnut Oil", "Farm-fresh groundnuts, slow wood-pressed to retain natural aroma and nutrition. Zero chemicals, zero preservatives.", 280.00, "1 Litre", 35),
  (2, "Sri Renuka Wood-Pressed Groundnut Oil", "Farm-fresh groundnuts, slow wood-pressed to retain natural aroma and nutrition. Zero chemicals, zero preservatives.", 150.00, "500 ml", 50),
  (2, "Sri Renuka Wood-Pressed Groundnut Oil", "Farm-fresh groundnuts, slow wood-pressed to retain natural aroma and nutrition. Zero chemicals, zero preservatives.", 830.00, "5 Litre (Family Pack)", 0);
