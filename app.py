from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask import redirect
import mysql.connector
import json
from datetime import datetime, timedelta , timezone
pkt = timezone(timedelta(hours=5))
import pytz
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import MultiDict
import os
import requests

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GEMINI_API_KEY = "AIzaSyAKdEVX6WEDiDkj685-v2biWttOkorIgiA"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='123abc',
    database='student_portal'
)
cursor = conn.cursor(dictionary=True)

# Define PKT timezone
pkt = pytz.timezone('Asia/Karachi')

# ---------------------- Static Routes ----------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/lesson')
def lesson():
    return render_template('lesson.html')

@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/teacher_upload_lesson')
def teacher_upload_lesson_page():
    return render_template('teacher_upload_lesson.html')

@app.route('/teacher_assignment')
def teacher_assignment():
    return render_template('teacher_assignment.html')

@app.route('/teacher_quiz')
def teacher_quiz():
    return render_template('teacher_quiz.html')

@app.route('/teacher_ai_quiz')
def teacher_ai_quiz():
    return render_template('teacher_ai_quiz.html')

@app.route('/upload_assignment')
def upload_assignment_page():
    return render_template('upload_assignment.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/assignment')
def assignment():
    return render_template('assignment.html')

@app.route('/teacher_upload_quiz')
def teacher_upload_quiz():
    return render_template('teacher_upload_quiz.html')

@app.route('/teacher/upload_quiz', methods=['GET'])
def upload_quiz_form():
    return render_template('teacher_upload_quiz.html')

# ---------------------- Auth ----------------------

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    # Fetch user from DB
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        if check_password_hash(user['password'], password):  # If you stored hashed passwords
            return jsonify({
                "message": "Login successful!",
                "role": user['role']
            }), 200
        else:
            return jsonify({"message": "Invalid password"}), 401
    else:
        return jsonify({"message": "User not found"}), 404

# Example signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data['name']
    email = data['email']
    raw_password = data['password']
    hashed_password = generate_password_hash(raw_password)  # 🔐 Hash password
    role = data['role']

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )
        conn.commit()
        return jsonify({"message": "Account created successfully!"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Email already registered."}), 409


# ---------------------- Gemini API ----------------------

def call_gemini_api(prompt_text):
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    if response.status_code != 200:
        print("Gemini error:", response.text)
        return None
    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Parsing error:", e)
        return None

# ----------------------------------------------
# Generate Lesson
# ----------------------------------------------

@app.route('/generate_lesson', methods=['POST'])
def generate_lesson():
    data = request.get_json()
    topic, email = data.get('topic'), data.get('email')

    if not topic or not email:
        return jsonify({"error": "Topic and Email are required"}), 400

    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id = user['id']

        prompt = f"""
    Generate a well-structured lesson for the topic: {topic}.

    Requirements:
    - Use clear section headings for:
        - Lesson Title
        - Objectives
        - Explanation or Main Content
        - Examples or Activities
        - Further Reading or YouTube links
    - Use numbered or bullet lists where suitable.
    - Under "Further Reading," include at least 2 relevant YouTube video links or reputable study resources related to the topic.
    - Format the links using Markdown so they appear clickable (e.g. [Title](https://link.com)).
    - Keep the language simple, suitable for middle school or high school students.
    - Keep the length under 600 words.
    - Do NOT use any extra symbols like # or * for headings or lists; use plain text and numbers/letters only.
    - Do NOT include any extra preambles, disclaimers, or formatting symbols.

    Return the lesson as clean Markdown, aligned to the above requirements.
    """
        lesson_content = call_gemini_api(prompt)

        if not lesson_content:
            return jsonify({"error": "Error generating lesson."}), 500

        cursor.execute(
            "INSERT INTO lessons (user_id, email, topic, content) VALUES (%s, %s, %s, %s)",
            (user_id, email, topic, lesson_content)
        )
        conn.commit()

        return jsonify({"content": lesson_content})

    except Exception as e:
        print(f"Error generating lesson: {e}")
        return jsonify({"error": "Something went wrong while generating the lesson."}), 500

# -------------------------------
# Teacher uploads quiz manually
# -------------------------------
@app.route('/teacher/upload_quiz', methods=['POST'])
def upload_quiz():
    try:
        lesson_number = request.form.get('lesson_number')
        title = request.form.get('title')

        raw = MultiDict(request.form)
        grouped_questions = []
        index = 0
        while f'questions[{index}][question]' in raw:
            # Convert naive string to aware datetime
            scheduled_str = raw.get(f'questions[{index}][scheduled_datetime]')
            # Accept both 'YYYY-MM-DDTHH:MM' and 'YYYY-MM-DD HH:MM:SS'
            try:
                if 'T' in scheduled_str:
                    scheduled_dt = datetime.strptime(scheduled_str, '%Y-%m-%dT%H:%M')
                else:
                    scheduled_dt = datetime.strptime(scheduled_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print("Datetime parse error:", e)
                raise

            grouped_questions.append({
                'question': raw.get(f'questions[{index}][question]'),
                'option_a': raw.get(f'questions[{index}][option_a]'),
                'option_b': raw.get(f'questions[{index}][option_b]'),
                'option_c': raw.get(f'questions[{index}][option_c]'),
                'option_d': raw.get(f'questions[{index}][option_d]'),
                'correct_option': raw.get(f'questions[{index}][correct_option]'),
                'scheduled_datetime': scheduled_dt
            })
            index += 1

        for q in grouped_questions:
            cursor.execute("""
                INSERT INTO class_quiz_questions 
                (lesson_number, title, question, option_a, option_b, option_c, option_d, correct_option, scheduled_datetime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lesson_number,
                title,
                q['question'],
                q['option_a'],
                q['option_b'],
                q['option_c'],
                q['option_d'],
                q['correct_option'],
                q['scheduled_datetime'].astimezone(pkt).strftime('%Y-%m-%d %H:%M:%S')
            ))

        conn.commit()
        return "Quiz uploaded successfully!"
    except Exception as e:
        print("Error uploading quiz:", e)
        return "Error uploading quiz.", 500



# -------------------------------
# Get quiz schedule
# -------------------------------
@app.route('/get_quiz_schedule', methods=['GET'])
def get_quiz_schedule():
    try:
        cursor.execute("""
            SELECT lesson_number, MIN(scheduled_datetime) AS scheduled_datetime
            FROM class_quiz_questions
            GROUP BY lesson_number
            ORDER BY lesson_number ASC
        """)
        quizzes = cursor.fetchall()

        for quiz in quizzes:
            # parse if coming as string
            if isinstance(quiz['scheduled_datetime'], str):
                quiz_time = datetime.strptime(quiz['scheduled_datetime'], '%Y-%m-%d %H:%M:%S')
                quiz_time = quiz_time.replace(tzinfo=pkt)
            else:
                quiz_time = quiz['scheduled_datetime']
                if quiz_time.tzinfo is None:
                    quiz_time = quiz_time.replace(tzinfo=pkt)

            # Return as PKT string instead of isoformat
            quiz['scheduled_datetime'] = quiz_time.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(quizzes)
    except Exception as e:
        print(f"Error loading quiz schedule: {e}")
        return jsonify([]), 500

@app.route('/get_quiz_questions', methods=['POST'])
def get_quiz_questions():
    data = request.get_json()
    lesson_number = data.get('lesson_number')
    email = data.get('email')

    try:
        # Get scheduled time
        cursor.execute("""
            SELECT MIN(scheduled_datetime) AS scheduled_time
            FROM class_quiz_questions
            WHERE lesson_number = %s
        """, (lesson_number,))
        result = cursor.fetchone()

        if not result or not result['scheduled_time']:
            return jsonify({"message": "Quiz not scheduled."}), 404

        scheduled_time = result['scheduled_time']

        # Ensure timezone is PKT
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.strptime(
                scheduled_time, '%Y-%m-%d %H:%M:%S'
            )
            scheduled_time = pkt.localize(scheduled_time)
        elif scheduled_time.tzinfo is None:
            scheduled_time = pkt.localize(scheduled_time)
        else:
            scheduled_time = scheduled_time.astimezone(pkt)

        now = datetime.now(pkt)

        quiz_open = scheduled_time
        quiz_close = scheduled_time + timedelta(minutes=3)

        # Check time window
        if now < quiz_open:
            return jsonify({"message": "Quiz not yet open.", "window": False}), 200

        if now > quiz_close:
            return jsonify({"message": "Quiz time has expired.", "window": False}), 200

        # Check if already submitted
        cursor.execute("""
            SELECT * FROM quiz_submissions
            WHERE lesson_number = %s AND user_id = (
                SELECT id FROM users WHERE email = %s
            )
        """, (lesson_number, email))
        submission = cursor.fetchone()

        if submission:
            return jsonify({"message": "You have already submitted this quiz.", "window": False}), 200

        # Fetch quiz questions
        cursor.execute("""
            SELECT * FROM class_quiz_questions
            WHERE lesson_number = %s
        """, (lesson_number,))
        questions = cursor.fetchall()

        return jsonify({
            "message": "Quiz loaded successfully.",
            "window": True,
            "questions": questions
        })

    except Exception as e:
        print(f"Error fetching quiz questions: {e}")
        return jsonify({"message": "Server error."}), 500


# -------------------------------
# Submit quiz (deadline check)
# -------------------------------
@app.route('/submit_class_quiz', methods=['POST'])
def submit_class_quiz():
    data = request.get_json()
    answers = data.get("answers")
    email = data.get("email")
    lesson_number = data.get("lesson_number")

    if not email or not lesson_number or not answers:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Get scheduled time
        cursor.execute("""
            SELECT MIN(scheduled_datetime) AS scheduled_time
            FROM class_quiz_questions
            WHERE lesson_number = %s
        """, (lesson_number,))
        result = cursor.fetchone()

        if not result or not result['scheduled_time']:
            return jsonify({"error": "Quiz not found."}), 404

        scheduled_time = result['scheduled_time']

        # Ensure timezone is PKT
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.strptime(
                scheduled_time, '%Y-%m-%d %H:%M:%S'
            )
            scheduled_time = pkt.localize(scheduled_time)
        elif scheduled_time.tzinfo is None:
            scheduled_time = pkt.localize(scheduled_time)
        else:
            scheduled_time = scheduled_time.astimezone(pkt)

        now = datetime.now(pkt)

        quiz_open = scheduled_time
        quiz_close = scheduled_time + timedelta(minutes=3)

        # Check time window
        if now < quiz_open:
            return jsonify({"error": "Quiz not yet open."}), 403

        if now > quiz_close:
            return jsonify({"error": "Submission window has expired."}), 403

        # Get user
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found."}), 400

        user_id = user['id']

        # Check duplicate submission
        cursor.execute("""
            SELECT * FROM quiz_submissions
            WHERE lesson_number = %s AND user_id = %s
        """, (lesson_number, user_id))
        submission = cursor.fetchone()

        if submission:
            return jsonify({"error": "You have already submitted this quiz."}), 403

        # Calculate score
        score = 0
        for answer in answers:
            cursor.execute("""
                SELECT correct_option FROM class_quiz_questions
                WHERE id = %s
            """, (answer['id'],))
            correct = cursor.fetchone()
            if correct and correct['correct_option'] == answer['selected']:
                score += 1

        total_questions = len(answers)

        # Save submission
        cursor.execute("""
            INSERT INTO quiz_submissions
            (user_id, lesson_number, quiz_title, score, total_questions)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id, lesson_number, "Class Quiz", score, total_questions
        ))

        conn.commit()
        return jsonify({"score": score})

    except Exception as e:
        print(f"Error submitting quiz: {e}")
        return jsonify({"error": "Server error."}), 500



# -------------------------------
# AI-generated quiz upload
# -------------------------------
@app.route('/teacher/generate_and_upload_quiz', methods=['POST'])
def generate_and_upload_quiz():
    data = request.get_json()
    topic = data.get("topic")
    lesson_number = data.get("lesson_number")
    scheduled_datetime = data.get("scheduled_datetime")

    prompt = f"""
    Generate 5 multiple-choice questions on the topic "{topic}". 
    Return ONLY a JSON array of objects in this exact format:

    [
      {{
        "question": "string",
        "option_a": "string",
        "option_b": "string",
        "option_c": "string",
        "option_d": "string",
        "correct_option": "A"
      }},
      ...
    ]

    The correct_option should ONLY be "A", "B", "C", or "D". 
    Do NOT include any explanations or markdown or any text before or after the JSON.
    """

    quiz_json_str = call_gemini_api(prompt)

    if not quiz_json_str or not quiz_json_str.strip():
        print("Gemini returned empty response!")
        return jsonify({"error": "Gemini returned empty response"}), 500

    if quiz_json_str.startswith("```"):
        quiz_json_str = quiz_json_str.strip("` \n")
        lines = quiz_json_str.splitlines()
        if lines and lines[0].strip().lower() == "json":
            quiz_json_str = "\n".join(lines[1:])

    try:
        quiz_data = json.loads(quiz_json_str)
    except Exception as e:
        print("JSON parse error:", e)
        return jsonify({"error": f"Failed to parse Gemini JSON: {e}"}), 500

    try:
        for q in quiz_data:
            cursor.execute("""
                INSERT INTO class_quiz_questions 
                (lesson_number, title, question, option_a, option_b, option_c, option_d, correct_option, scheduled_datetime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lesson_number,
                topic,
                q['question'],
                q['option_a'],
                q['option_b'],
                q['option_c'],
                q['option_d'],
                q['correct_option'],
                scheduled_datetime
            ))
        conn.commit()

        return jsonify({"message": "AI quiz generated and uploaded successfully."})
    except Exception as e:
        print("Error saving AI quiz:", e)
        return jsonify({"error": "Server error while saving AI quiz."}), 500

    
# ----------------------------------------------
# Assignments
# ----------------------------------------------

@app.route('/get_scheduled_assignments', methods=['GET'])
def get_scheduled_assignments():
    try:
        cursor.execute("SELECT * FROM scheduled_assignments ORDER BY deadline ASC")
        return jsonify(cursor.fetchall())
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([]), 500

@app.route('/get_assignment_pdf/<filename>')
def get_assignment_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/submit_assignment', methods=['POST'])
def submit_assignment():
    assignment_id = request.form['assignment_id']
    user_email = request.form['user_email']
    file = request.files['file']

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    cursor.execute("INSERT INTO assignment_submissions (assignment_id, user_email, uploaded_file) VALUES (%s, %s, %s)",
                   (assignment_id, user_email, filename))
    conn.commit()

    return jsonify({"message": "Assignment submitted successfully!"})

@app.route('/admin/upload_assignment', methods=['GET', 'POST'])
def upload_assignment():
    email = request.args.get('email')
    if not email:
        return "Unauthorized - No email provided", 401

    cursor.execute("SELECT role FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user or user['role'] != 'admin':
        return "Forbidden - Admin access required", 403

    if request.method == 'POST':
        lesson_number = request.form['lesson_number']
        title = request.form['title']
        description = request.form['description']
        deadline = request.form['deadline']
        pdf = request.files['pdf_file']

        if pdf and pdf.filename.endswith('.pdf'):
            filename = secure_filename(pdf.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf.save(save_path)

            cursor.execute("""
                INSERT INTO scheduled_assignments (lesson_number, title, description, pdf_filename, deadline)
                VALUES (%s, %s, %s, %s, %s)
            """, (lesson_number, title, description, filename, deadline))
            conn.commit()

            return "Assignment uploaded successfully."
        else:
            return "Only PDF files are allowed."

    return render_template('upload_assignment.html')

# Generate practice assignment using Gemini
@app.route('/generate_practice_assignment', methods=['POST'])
def generate_practice_assignment():
    topic = request.get_json().get("topic")
    prompt = f"""Give a short practice assignment question for the topic: {topic}.
    Do NOT use any extra symbols like # or * for headings or lists; use plain text and numbers/letters only."""
    question = call_gemini_api(prompt)
    return jsonify({"question": question}) if question else jsonify({"question": "Error generating assignment"}), 500

# Evaluate practice assignment using Gemini
@app.route('/evaluate_practice_assignment', methods=['POST'])
def evaluate_practice_assignment():
    data = request.get_json()
    question, answer = data.get("question"), data.get("answer")

    prompt = (
        f"Evaluate the following student's answer.\n\n"
        f"Question: {question}\n\n"
        f"Student Answer: {answer}\n\n"
        "If the answer is incorrect or the student does not know the answer, provide the correct answer as part of your feedback. "
        "Provide constructive feedback. "
        "Do NOT use any extra symbols like # or * for headings or lists; use plain text and numbers/letters only."
    )
    feedback = call_gemini_api(prompt)
    return jsonify({"feedback": feedback}) if feedback else jsonify({"feedback": "Error evaluating answer"}), 500

# ----------------------------------------------
# User Records
# ----------------------------------------------

@app.route('/get_user_lessons', methods=['GET'])
def get_user_lessons():
    email = request.args.get('email')
    if not email:
        return jsonify([]), 400

    try:
        cursor.execute("""
            SELECT topic, created_at
            FROM lessons
            WHERE email = %s
            ORDER BY created_at DESC
        """, (email,))
        lessons = cursor.fetchall()
        return jsonify(lessons)
    except Exception as e:
        print(f"Error fetching user lessons: {e}")
        return jsonify([]), 500

@app.route('/get_user_quiz_results', methods=['GET'])
def get_user_quiz_results():
    email = request.args.get('email')
    if not email:
        return jsonify([]), 400

    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify([])

        user_id = user['id']
        cursor.execute("""
            SELECT 
                qs.quiz_title as title,
                qs.lesson_number,
                qs.score,
                qs.total_questions,
                qs.submitted_at
            FROM quiz_submissions qs
            WHERE qs.user_id = %s
            ORDER BY qs.submitted_at DESC
        """, (user_id,))
        quizzes = cursor.fetchall()
        return jsonify(quizzes)

    except Exception as e:
        print(f"Error fetching quiz results: {e}")
        return jsonify([]), 500

@app.route('/get_user_assignments', methods=['GET'])
def get_user_assignments():
    email = request.args.get('email')
    if not email:
        return jsonify([]), 400

    try:
        cursor.execute("""
            SELECT 
                sa.title,
                sa.deadline,
                asub.uploaded_file,
                asub.submitted_at
            FROM assignment_submissions asub
            JOIN scheduled_assignments sa ON sa.id = asub.assignment_id
            WHERE asub.user_email = %s
            ORDER BY asub.submitted_at DESC
        """, (email,))
        assignments = cursor.fetchall()
        return jsonify(assignments)
    except Exception as e:
        print(f"Error fetching user assignments: {e}")
        return jsonify([]), 500

@app.route('/records')
def records():
    email = request.args.get('email')
    if not email:
        return "Email required", 400

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    user_id = user['id']

    # Fetch user's lessons
    cursor.execute("""
        SELECT topic, created_at
        FROM lessons
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    lessons = cursor.fetchall()

    # Fetch user's quiz submissions
    cursor.execute("""
        SELECT 
            lesson_number, 
            quiz_title, 
            score, 
            total_questions,      # <-- Add this line
            submitted_at
        FROM quiz_submissions
        WHERE user_id = %s
        ORDER BY submitted_at DESC
    """, (user_id,))
    quizzes = cursor.fetchall()

    # Fetch user's assignment submissions
    cursor.execute("""
        SELECT 
            s.title, 
            s.deadline, 
            a.uploaded_file, 
            a.submitted_at, 
            a.marks,
            a.comments
        FROM scheduled_assignments s
        JOIN assignment_submissions a 
            ON s.id = a.assignment_id
        WHERE a.user_email = %s
        ORDER BY a.submitted_at DESC
    """, (email,))
    assignments = cursor.fetchall()

    return render_template(
        "records.html", 
        lessons=lessons, 
        quizzes=quizzes, 
        assignments=assignments
    )

# ✅ Route to list all assignment submissions
@app.route('/admin/assignment_submissions')
def list_assignment_submissions():
    try:
        cursor.execute("""
            SELECT 
                asub.id AS submission_id,
                asub.user_email,
                u.name AS student_name,
                sa.title AS assignment_title,
                sa.lesson_number,
                asub.uploaded_file,
                asub.submitted_at,
                asub.marks,
                asub.comments
            FROM assignment_submissions asub
            JOIN users u ON u.email = asub.user_email
            JOIN scheduled_assignments sa ON sa.id = asub.assignment_id
            ORDER BY asub.submitted_at DESC
        """)
        submissions = cursor.fetchall()
        return render_template('assignment_submissions_list.html', submissions=submissions)
    except Exception as e:
        print("Error loading assignment submissions:", e)
        return "Error loading submissions", 500


# ✅ Route to show the Check Assignment page
@app.route('/admin/check_assignment/<int:submission_id>')
def check_assignment(submission_id):
    try:
        cursor.execute("""
            SELECT 
            asub.id AS submission_id,
            asub.user_email,
            u.name AS student_name,
            sa.title AS assignment_title,
            sa.lesson_number,
            asub.uploaded_file,
            asub.submitted_at,
            asub.marks,
            asub.comments
            FROM assignment_submissions asub
            JOIN users u ON u.email = asub.user_email
            JOIN scheduled_assignments sa ON sa.id = asub.assignment_id
            WHERE asub.id = %s
        """, (submission_id,))
        submission = cursor.fetchone()

        if not submission:
            return "Submission not found", 404

        return render_template('check_assignment.html', submission=submission)

    except Exception as e:
        print("Error loading assignment:", e)
        return "Error loading assignment.", 500


# ✅ Route to save teacher evaluation
@app.route('/admin/submit_evaluation', methods=['POST'])
def submit_evaluation():
    submission_id = request.form['submission_id']
    marks = request.form['marks']
    comments = request.form['comments']

    try:
        cursor.execute("""
            UPDATE assignment_submissions
            SET marks = %s, comments = %s
            WHERE id = %s
        """, (marks, comments, submission_id))
        conn.commit()
        return redirect('/admin/assignment_submissions')
    except Exception as e:
        print("Error saving evaluation:", e)
        return "Error saving evaluation.", 500

@app.route('/get_uploaded_lessons', methods=['GET'])
def get_uploaded_lessons():
    try:
        cursor.execute("SELECT lesson_number, title, pdf_filename FROM scheduled_assignments ORDER BY lesson_number ASC")
        lessons = cursor.fetchall()
        return jsonify(lessons)
    except Exception as e:
        print("Error fetching uploaded lessons:", e)
        return jsonify([]), 500

@app.route('/teacher/upload_lesson', methods=['POST'])
def teacher_upload_lesson():
    title = request.form.get('title')
    lesson_number = request.form.get('lesson_number')
    pdf = request.files.get('pdf_file')

    if not title or not lesson_number or not pdf:
        return jsonify({"error": "All fields are required."}), 400

    if not pdf.filename.endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed."}), 400

    filename = secure_filename(pdf.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf.save(save_path)

    try:
        cursor.execute("""
            INSERT INTO scheduled_assignments (lesson_number, title, pdf_filename)
            VALUES (%s, %s, %s)
        """, (lesson_number, title, filename))
        conn.commit()
        return jsonify({"message": "Lesson uploaded successfully."})
    except Exception as e:
        print("Error uploading lesson:", e)
        return jsonify({"error": "Server error while uploading lesson."}), 500

@app.route('/get_uploaded_lesson/<filename>')
def get_uploaded_lesson(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/teacher/see_results')
def teacher_see_results():
    # Get all students
    cursor.execute("SELECT id, name, email FROM users WHERE role = 'student' ORDER BY name ASC")
    students = cursor.fetchall()

    # For each student, get their quizzes and assignments
    results = []
    for student in students:
        # Quizzes
        cursor.execute("""
            SELECT lesson_number, quiz_title, score, total_questions, submitted_at
            FROM quiz_submissions
            WHERE user_id = %s
            ORDER BY submitted_at DESC
        """, (student['id'],))
        quizzes = cursor.fetchall()

        # Assignments
        cursor.execute("""
            SELECT sa.title, sa.lesson_number, a.marks, a.submitted_at
            FROM assignment_submissions a
            JOIN scheduled_assignments sa ON sa.id = a.assignment_id
            WHERE a.user_email = %s
            ORDER BY a.submitted_at DESC
        """, (student['email'],))
        assignments = cursor.fetchall()

        results.append({
            "student": student,
            "quizzes": quizzes,
            "assignments": assignments
        })

    return render_template('teacher_see_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)