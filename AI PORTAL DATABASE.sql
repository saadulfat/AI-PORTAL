-- Create and use database
CREATE DATABASE IF NOT EXISTS student_portal;
USE student_portal;

-- Set timezone
SET GLOBAL time_zone = '+05:00';
SET time_zone = '+05:00';

-- =============================
-- USERS TABLE
-- =============================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'student'
);

-- =============================
-- LESSONS TABLE
-- =============================
CREATE TABLE IF NOT EXISTS lessons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    email VARCHAR(100),
    topic VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================
-- UPLOADED LESSONS TABLE
-- =============================
CREATE TABLE IF NOT EXISTS uploaded_lessons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lesson_number INT,
    title VARCHAR(255),
    pdf_filename VARCHAR(255),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================
-- CLASS QUIZ QUESTIONS
-- =============================
CREATE TABLE IF NOT EXISTS class_quiz_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lesson_number INT NOT NULL,
    title VARCHAR(255),
    question TEXT NOT NULL,
    option_a VARCHAR(255),
    option_b VARCHAR(255),
    option_c VARCHAR(255),
    option_d VARCHAR(255),
    correct_option CHAR(1),
    scheduled_datetime DATETIME NOT NULL
);

-- =============================
-- QUIZ SUBMISSIONS
-- =============================
CREATE TABLE IF NOT EXISTS quiz_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    lesson_number INT NOT NULL,
    quiz_title VARCHAR(255) DEFAULT 'Class Quiz',
    score INT NOT NULL,
    total_questions INT DEFAULT 0,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_lesson (user_id, lesson_number),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =============================
-- SCHEDULED ASSIGNMENTS
-- =============================
CREATE TABLE IF NOT EXISTS scheduled_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lesson_number VARCHAR(50),
    title VARCHAR(255),
    description TEXT,
    pdf_filename VARCHAR(255),
    deadline DATETIME
);

-- =============================
-- ASSIGNMENT SUBMISSIONS
-- =============================
CREATE TABLE IF NOT EXISTS assignment_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT,
    user_email VARCHAR(255),
    uploaded_file VARCHAR(255),
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    marks INT,
    comments TEXT,
    FOREIGN KEY (assignment_id) REFERENCES scheduled_assignments(id)
);
