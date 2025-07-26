🧠 AI Portal
AI Portal is a full-stack web application that brings together student learning, quiz assessments, and AI-driven content generation. Built using Flask and powered by Google's Gemini API, it helps students interact with lessons, complete quizzes, and submit assignments – all through a simple web interface.

---------- FEATURES ----------
🔐 User Authentication – Secure login and registration with hashed passwords

📘 Lesson Management – Create, upload, and view text or PDF-based lessons

🧠 AI Content Generation – Integrated with Gemini API for generating content, explanations, or answers

📝 Assignments – Assignments can be scheduled and submitted with file uploads

📊 Quizzes – Teachers can schedule class quizzes; students can participate and get evaluated

📁 File Upload Support – Upload and store PDFs for lessons and assignments

⏰ Scheduling – Set deadlines for quizzes and assignments

🌐 API-Friendly – CORS enabled for integration with frontend apps (React, etc.)

---------- TECH STACK ----------
Backend: Python (Flask)
Frontend: HTML, CSS (with Jinja templates)
Database: MySQL
AI Integration: Google Gemini API
Libraries Used:

flask, flask-cors

mysql-connector-python

requests, werkzeug

---------- FOLDER STRUCTURE ----------
graphql
Copy
Edit
AI_PORTAL/
├── app.py                   # Main backend application
├── templates/               # HTML templates (Jinja2)
├── static/                  # CSS, JS, and images
├── uploads/                 # Uploaded PDFs and assignment files
├── style.css                # Global styling
├── student_portal.sql       # Database schema (if provided)
└── .git/                    # Git version control folder
---------- DATABASE STRUCTURE ----------
1. users
Stores registered users

sql
Copy
Edit
(id, name, email, password, role)
2. lessons
Stores text-based lessons

sql
Copy
Edit
(id, user_id, email, topic, content, created_at)
3. uploaded_lessons
Stores lesson PDFs

sql
Copy
Edit
(id, lesson_number, title, pdf_filename, uploaded_at)
4. class_quiz_questions
Holds scheduled quiz questions

sql
Copy
Edit
(id, lesson_number, question, options A–D, correct_option, scheduled_datetime)
5. quiz_submissions
Student quiz responses and scores

sql
Copy
Edit
(id, user_id, lesson_number, score, submitted_at)
6. scheduled_assignments
Assignments created by teachers

sql
Copy
Edit
(id, lesson_number, title, pdf_filename, deadline)
7. assignment_submissions
Student assignment submissions

sql
Copy
Edit
(id, assignment_id, user_email, uploaded_file, submitted_at, marks, comments)
---------- SETUP INSTRUCTIONS ----------
Step 1: Clone the repo

bash
Copy
Edit
git clone https://github.com/yourusername/ai-portal.git
cd ai-portal
Step 2: Create a virtual environment (optional but recommended)

bash
Copy
Edit
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
Step 3: Install dependencies

bash
Copy
Edit
pip install flask flask-cors mysql-connector-python requests
Step 4: Set up MySQL

Create a database:

sql
Copy
Edit
CREATE DATABASE student_portal;
Import the schema (if file available):

bash
Copy
Edit
mysql -u root -p student_portal < student_portal.sql
Update DB credentials in app.py:

python
Copy
Edit
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='your_password',
    database='student_portal'
)
Step 5: Run the app

bash
Copy
Edit
python app.py
Visit: http://localhost:5000

---------- AI API INTEGRATION (Gemini) ----------
To enable AI features, you need a Gemini API Key.

Get your API key from: https://makersuite.google.com/app

Add it to app.py:

python
Copy
Edit
GEMINI_API_KEY = "your_api_key_here"
The app uses:

bash
Copy
Edit
https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
---------- HOW TO USE ----------
✅ Register or Login

📤 Upload new lessons (text or PDFs)

📚 View all lessons

🧠 Use AI to generate content or explanations

📝 Attempt scheduled quizzes

📁 Submit assignment PDFs

📊 View scores (if available)

---------- FUTURE IMPROVEMENTS ----------
🔐 JWT-based session auth

🧑‍🏫 Admin/Teacher dashboards

📄 PDF-to-text AI summarization

⏱️ Live quiz timers

📲 React frontend or mobile UI

🐳 Docker containerization

📬 Email notifications (assignments/quizzes)

---------- LICENSE ----------
This project is open source under the MIT License.
Feel free to use, contribute, and adapt to your needs.
