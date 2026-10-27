-- =====================================================================
-- Library Management System - Database Schema & Initial Seed Data
-- =====================================================================

CREATE DATABASE IF NOT EXISTS library_management_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE library_management_db;

-- 1. Users Table (Librarians & Admins)
CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  role ENUM('admin', 'librarian', 'assistant') DEFAULT 'librarian',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Books Table
CREATE TABLE IF NOT EXISTS books (
  book_id INT AUTO_INCREMENT PRIMARY KEY,
  isbn VARCHAR(20) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  author VARCHAR(150) NOT NULL,
  category VARCHAR(80) NOT NULL,
  publication_year INT NOT NULL,
  total_copies INT NOT NULL DEFAULT 1,
  available_copies INT NOT NULL DEFAULT 1,
  shelf_location VARCHAR(50) DEFAULT 'Section A',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_isbn (isbn),
  INDEX idx_title (title),
  INDEX idx_author (author),
  INDEX idx_category (category)
) ENGINE=InnoDB;

-- 3. Students Table
CREATE TABLE IF NOT EXISTS students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  student_number VARCHAR(30) NOT NULL UNIQUE,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  phone VARCHAR(20) NOT NULL,
  department VARCHAR(80) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_student_number (student_number)
) ENGINE=InnoDB;

-- 4. Book Issues Table
CREATE TABLE IF NOT EXISTS book_issues (
  issue_id INT AUTO_INCREMENT PRIMARY KEY,
  book_id INT NOT NULL,
  student_id INT NOT NULL,
  issue_date DATE NOT NULL,
  due_date DATE NOT NULL,
  return_date DATE NULL,
  status ENUM('issued', 'returned', 'overdue') DEFAULT 'issued',
  fine_amount DECIMAL(6, 2) DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
  INDEX idx_issue_status (status)
) ENGINE=InnoDB;

-- 5. Reservations Table (For FIFO Queue)
CREATE TABLE IF NOT EXISTS reservations (
  reservation_id INT AUTO_INCREMENT PRIMARY KEY,
  book_id INT NOT NULL,
  student_id INT NOT NULL,
  reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  queue_position INT NOT NULL DEFAULT 1,
  status ENUM('pending', 'fulfilled', 'cancelled') DEFAULT 'pending',
  FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
  INDEX idx_res_status (status),
  INDEX idx_res_queue (book_id, queue_position)
) ENGINE=InnoDB;

-- 6. Transactions Audit Table (For LIFO Stack Undo)
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id INT AUTO_INCREMENT PRIMARY KEY,
  action_type VARCHAR(50) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id INT NOT NULL,
  details JSON NULL,
  user_id INT NULL,
  undone TINYINT(1) DEFAULT 0,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
  INDEX idx_tx_timestamp (timestamp)
) ENGINE=InnoDB;

-- 7. Book Relations Table (For Graph Recommendations & BFS/DFS)
CREATE TABLE IF NOT EXISTS book_relations (
  relation_id INT AUTO_INCREMENT PRIMARY KEY,
  source_book_id INT NOT NULL,
  target_book_id INT NOT NULL,
  relation_type VARCHAR(50) NOT NULL DEFAULT 'co_borrowed',
  weight DECIMAL(3, 2) DEFAULT 1.00,
  FOREIGN KEY (source_book_id) REFERENCES books(book_id) ON DELETE CASCADE,
  FOREIGN KEY (target_book_id) REFERENCES books(book_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_relation (source_book_id, target_book_id)
) ENGINE=InnoDB;

-- =====================================================================
-- Seed Data
-- =====================================================================

-- Default Administrator (Password: admin123)
-- Hash generated using scrypt/pbkdf2 via werkzeug.security
INSERT INTO users (username, password_hash, full_name, email, role)
VALUES 
('admin', 'scrypt:32768:8:1$9wdvIxbntQrbbFyI$2855f52f6803bc01c143931f74b60f85c352d88a17896c8d79a25d6c9c0e35f5572f31f1e27bbc6505c83f48a5805854bf77d8e50bbb78bd9e5fc5967b4aaff2', 'Chief Librarian Harishma', 'admin@library.edu', 'admin'),
('librarian', 'scrypt:32768:8:1$9wdvIxbntQrbbFyI$2855f52f6803bc01c143931f74b60f85c352d88a17896c8d79a25d6c9c0e35f5572f31f1e27bbc6505c83f48a5805854bf77d8e50bbb78bd9e5fc5967b4aaff2', 'Assistant Librarian John', 'john@library.edu', 'librarian')
ON DUPLICATE KEY UPDATE username=username;

-- Seed Books
INSERT INTO books (book_id, isbn, title, author, category, publication_year, total_copies, available_copies, shelf_location) VALUES
(1, '978-0262033848', 'Introduction to Algorithms', 'Thomas H. Cormen', 'Computer Science', 2009, 5, 3, 'Shelf CS-01'),
(2, '978-0132350884', 'Clean Code', 'Robert C. Martin', 'Software Engineering', 2008, 4, 4, 'Shelf SE-03'),
(3, '978-0131103627', 'The C Programming Language', 'Brian W. Kernighan', 'Programming', 1988, 3, 2, 'Shelf PR-02'),
(4, '978-0201633610', 'Design Patterns', 'Erich Gamma', 'Software Engineering', 1994, 4, 3, 'Shelf SE-04'),
(5, '978-1449355739', 'Learning Python', 'Mark Lutz', 'Programming', 2013, 6, 5, 'Shelf PR-05'),
(6, '978-0134685991', 'Effective Java', 'Joshua Bloch', 'Programming', 2017, 3, 3, 'Shelf PR-06'),
(7, '978-0262035613', 'Deep Learning', 'Ian Goodfellow', 'Artificial Intelligence', 2016, 4, 3, 'Shelf AI-01'),
(8, '978-1491957660', 'Hands-On Machine Learning', 'Aurélien Géron', 'Artificial Intelligence', 2019, 5, 4, 'Shelf AI-02'),
(9, '978-0321573513', 'Algorithms 4th Edition', 'Robert Sedgewick', 'Computer Science', 2011, 4, 3, 'Shelf CS-02'),
(10, '978-0133594140', 'Operating System Concepts', 'Abraham Silberschatz', 'Systems', 2018, 5, 4, 'Shelf OS-01')
ON DUPLICATE KEY UPDATE book_id=book_id;

-- Seed Students
INSERT INTO students (student_id, student_number, full_name, email, phone, department) VALUES
(1, 'STU2026001', 'Alice Johnson', 'alice.j@student.edu', '9876543210', 'Computer Science & Engg'),
(2, 'STU2026002', 'Brian Miller', 'brian.m@student.edu', '9876543211', 'Information Technology'),
(3, 'STU2026003', 'Catherine Davis', 'catherine.d@student.edu', '9876543212', 'Artificial Intelligence & DS'),
(4, 'STU2026004', 'David Wilson', 'david.w@student.edu', '9876543213', 'Computer Science & Engg'),
(5, 'STU2026005', 'Elena Rostova', 'elena.r@student.edu', '9876543214', 'Electronics & Comm Engg')
ON DUPLICATE KEY UPDATE student_id=student_id;

-- Seed Active Book Issues
INSERT INTO book_issues (issue_id, book_id, student_id, issue_date, due_date, return_date, status, fine_amount) VALUES
(1, 1, 1, '2026-10-10', '2026-10-24', NULL, 'overdue', 15.00),
(2, 1, 2, '2026-10-18', '2026-11-01', NULL, 'issued', 0.00),
(3, 3, 3, '2026-10-20', '2026-11-03', NULL, 'issued', 0.00),
(4, 7, 4, '2026-10-22', '2026-11-05', NULL, 'issued', 0.00),
(5, 4, 5, '2026-10-15', '2026-10-29', NULL, 'issued', 0.00)
ON DUPLICATE KEY UPDATE issue_id=issue_id;

-- Seed Reservations (FIFO Queue)
INSERT INTO reservations (reservation_id, book_id, student_id, reservation_date, queue_position, status) VALUES
(1, 1, 3, '2026-10-21 09:30:00', 1, 'pending'),
(2, 1, 4, '2026-10-22 14:15:00', 2, 'pending'),
(3, 1, 5, '2026-10-23 11:00:00', 3, 'pending'),
(4, 3, 2, '2026-10-24 16:45:00', 1, 'pending')
ON DUPLICATE KEY UPDATE reservation_id=reservation_id;

-- Seed Book Graph Relations (Recommendations)
-- Edges representing relationships: Related algorithms, same author, or frequently borrowed together
INSERT INTO book_relations (source_book_id, target_book_id, relation_type, weight) VALUES
(1, 9, 'Same Topic: Algorithms', 0.95),
(9, 1, 'Same Topic: Algorithms', 0.95),
(1, 10, 'Prerequisite: CS Core', 0.80),
(10, 1, 'Prerequisite: CS Core', 0.80),
(2, 4, 'Same Domain: Software Architecture', 0.90),
(4, 2, 'Same Domain: Software Architecture', 0.90),
(2, 6, 'Clean Code Best Practices', 0.85),
(6, 2, 'Clean Code Best Practices', 0.85),
(3, 10, 'C & Low-level Operating Systems', 0.88),
(10, 3, 'C & Low-level Operating Systems', 0.88),
(5, 7, 'Python Foundation for AI', 0.85),
(7, 5, 'Python Foundation for AI', 0.85),
(7, 8, 'Machine Learning & Deep Learning', 0.98),
(8, 7, 'Machine Learning & Deep Learning', 0.98),
(8, 5, 'Hands-on Python Implementation', 0.82),
(5, 8, 'Hands-on Python Implementation', 0.82),
(1, 7, 'Algorithmic Foundation for AI', 0.75),
(7, 1, 'Algorithmic Foundation for AI', 0.75)
ON DUPLICATE KEY UPDATE relation_id=relation_id;
