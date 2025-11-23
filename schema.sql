-- Drop existing tables if any
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

-- Create tables
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob DATE,
    email TEXT UNIQUE
);

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    credits INTEGER
);

CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    course_id INTEGER REFERENCES courses(id),
    enrolled_on DATE,
    grade TEXT
);

-- Insert students
INSERT INTO students (first_name, last_name, dob, email) VALUES
('John','Doe','2000-01-01','john@example.com'),
('Aisha','Khan','2002-03-09','aisha@example.com'),
('Ravi','Patel','2001-07-21','ravi@example.com'),
('Meera','Sharma','2003-11-12','meera.sharma@example.com'),
('Arjun','Nair','1999-06-15','arjun.nair@example.com'),
('Fatima','Hussain','2002-12-22','fatima.h@example.com'),
('Daniel','Fernandes','2001-04-03','dan.fernandes@example.com'),
('Sofia','Reddy','2000-09-14','sofia.reddy@example.com'),
('Karan','Malhotra','1998-05-27','karan.mal@example.com'),
('Lina','Joseph','2001-01-30','lina.j@example.com');

-- Insert courses
INSERT INTO courses (code, title, credits) VALUES
('CS101','Intro to Computer Science',4),
('CS102','Data Structures',4),
('CS201','Algorithms',4),
('MATH101','Calculus I',3),
('MATH102','Linear Algebra',3),
('PHY101','Physics Basics',3),
('ENG101','English Literature',2),
('BIO101','General Biology',3),
('HIST101','World History',2),
('ECON101','Microeconomics',3);

-- Insert enrollments
INSERT INTO enrollments (student_id, course_id, enrolled_on, grade) VALUES
(1, 1, '2025-01-10', 'A'),
(1, 3, '2025-01-10', 'B+'),
(1, 4, '2025-01-10', 'A-'),
(2, 1, '2025-01-11', 'B'),
(2, 2, '2025-01-11', 'A'),
(2, 5, '2025-01-11', 'B+'),
(3, 3, '2025-01-12', 'A-'),
(3, 4, '2025-01-12', 'C+'),
(4, 2, '2025-01-13', 'B'),
(4, 3, '2025-01-13', 'A'),
(4, 9, '2025-01-13', 'A-'),
(5, 1, '2025-01-14', 'B-'),
(5, 8, '2025-01-14', 'A'),
(6, 2, '2025-01-15', 'A'),
(6, 3, '2025-01-15', 'A-'),
(7, 1, '2025-01-16', 'B+'),
(7, 6, '2025-01-16', 'C'),
(8, 4, '2025-01-17', 'A'),
(8, 5, '2025-01-17', 'B'),
(9, 7, '2025-01-18', 'A-'),
(9, 8, '2025-01-18', 'B+'),
(10, 1, '2025-01-19', 'C+'),
(10, 10, '2025-01-19', 'B');
