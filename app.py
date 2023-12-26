from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import flash
from datetime import datetime, timedelta,date
import re
from collections import Counter


app = Flask(__name__)
app.secret_key = 'xyzsdfg'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'muqadas2024????'
app.config['MYSQL_DB'] = 'student_interest_system'
mysql = MySQL(app)


@app.route('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password,))
        user = cursor.fetchone()
        if user:
            print("Login successful!")
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            print("Accessing the dashboard...")
            if 'loggedin' in session:
                print("User is logged in.")
                interest_count = get_unique_interest_count()
                top_interests = get_top_interests()
                bottom_interest=get_bottom_interests()
                provincial_distribution = get_provincial_distribution()
                department_distribution = get_department_distribution()
                gender_distribution = get_gender_distribution()
                degree_title_distribution = get_degree_title_distribution()
                daily_submission = get_daily_submission()
                student_counts = get_student_status_counts()
                age_distribution = get_age_distribution()

                print(f"Interest count from dashboard: {interest_count}")
                print(f"Top 5 interest from dashboard: {top_interests}")
                print(f"Bottom 5 interest from dashboard: {bottom_interest}")
                if interest_count is not None or daily_submission is not None:
                    distinct_interests = get_unique_interest_count()
                    return render_template('dashboard.html', distinct_interests=distinct_interests,
                                           top_interests = top_interests,bottom_interest=bottom_interest,
                                           provincial_distribution=provincial_distribution,
                                           department_distribution =department_distribution,
                                           gender_distribution=gender_distribution,
                                           degree_title_distribution=degree_title_distribution
                                           , daily_submission=daily_submission
                                           , age_distribution=age_distribution
                                           , student_counts= student_counts
                                           )
                else:
                    flash("Error fetching interest count.", "danger")
                    return render_template('dashboard.html', interest_count=0,top_interests =0,bottom_interest=0)
        else:
            print("Login failed. Incorrect email or password.")
            message = 'Email or password is not correct.'
    return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO user (name, email, password) VALUES (%s, %s, %s)', (userName, email, password,))
        mysql.connection.commit()
        message = 'You have successfully registered!'
        return render_template('login.html', message=message)
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

def get_student_status_counts():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN end_date >= CURDATE() THEN 1 END) AS currently_studying,
                COUNT(CASE WHEN start_date >= CURDATE() AND end_date >= CURDATE() THEN 1 END) AS recently_enrolled,
                COUNT(CASE WHEN end_date >= CURDATE() AND end_date <= CURDATE() + INTERVAL 30 DAY THEN 1 END) AS about_to_graduate,
                COUNT(CASE WHEN end_date < CURDATE() THEN 1 END) AS graduated
            FROM students
        ''')
        student_counts = cursor.fetchone()
        cursor.close()
        return student_counts
    except Exception as e:
        print(f"Error: {e}")
        return None


def calculate_age(dob):
    today = date.today()
    birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def get_age_distribution():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT dob FROM students')
        dob_list = cursor.fetchall()
        cursor.close()
        # Filter out invalid date of birth values
        valid_dob_list = [dob['dob'] for dob in dob_list if dob['dob'] is not None and isinstance(dob['dob'], str)]
        # Calculate ages from valid date of birth values
        ages = [calculate_age(dob) for dob in valid_dob_list]
        # Count occurrences of each age
        age_counts = Counter(ages)
        return age_counts
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_provincial_distribution():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT city, COUNT(city) as count FROM students GROUP BY city')
        provincial_distribution = cursor.fetchall()
        cursor.close()
        return provincial_distribution
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_daily_submission():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Query to get the count of students created daily in the last 30 days
        cursor.execute('''
            SELECT DATE(start_date) AS submission_date, COUNT(*) AS count
            FROM students
            WHERE start_date >= %s
            GROUP BY submission_date
            ORDER BY submission_date
        ''', (datetime.now() - timedelta(days=30),))
        daily_submission = cursor.fetchall()
        cursor.close()
        return daily_submission
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_department_distribution():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT department, COUNT(department) as count FROM students GROUP BY department')
        department_distribution = cursor.fetchall()
        cursor.close()
        return department_distribution
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_degree_title_distribution():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT degree_title, COUNT(degree_title) as count FROM students GROUP BY degree_title')
        degree_title_distribution = cursor.fetchall()
        cursor.close()
        return degree_title_distribution
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_gender_distribution():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT gender, COUNT(gender) as count FROM students GROUP BY gender')
        gender_distribution = cursor.fetchall()
        cursor.close()
        return gender_distribution
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_bottom_interests(limit=5):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT interest, COUNT(interest) as count FROM students GROUP BY interest ORDER BY count ASC LIMIT %s', (limit,))
        bottom_interests = cursor.fetchall()
        cursor.close()
        return bottom_interests
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_unique_interest_count():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT interest, COUNT(interest) as interest_count FROM students GROUP BY interest')
        distinct_interests = {row['interest']: row['interest_count'] for row in cursor.fetchall()}
        cursor.close()
        return distinct_interests
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_top_interests(limit=5):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT interest, COUNT(interest) as count FROM students GROUP BY interest ORDER BY count DESC LIMIT %s', (limit,))
        top_interests = cursor.fetchall()
        cursor.close()
        return top_interests
    except Exception as e:
        print(f"Error: {e}")
        return None


@app.route('/dashboard')
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        return f"An error occurred: {str(e)}"



@app.route('/addStudentPage')
def add_student_page():
    if 'loggedin' in session:
        return render_template('add_student.html')
    else:
        return redirect(url_for('login'))


@app.route('/addStudent', methods=['GET', 'POST'])
def add_student():
    if 'loggedin' in session:
        if request.method == 'POST':
            # Extract data from the form
            full_name = request.form['full_name']
            roll_number = request.form['roll_number']
            email = request.form['email']
            gender = request.form['gender']
            dob = request.form['dob']
            city = request.form['city']
            interest = request.form['interest']
            custom_interest = request.form.get('custom_interest', None)
            department = request.form['department']
            degree_title = request.form['degree_title']
            subject = request.form['subject']
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            # Check if all required fields are filled
            if not all([full_name, roll_number, email, gender, dob, city, interest, department, degree_title, subject, start_date, end_date]):
                flash('Please fill in all fields.', 'danger')
                return render_template('add_student.html')

            # If the selected interest is "custom," use the custom interest value
            if interest.lower() == "custom" and custom_interest:
                # Use custom_interest if provided
                interest = clean_interest(custom_interest)
            else:
                # Use the selected interest as is
                interest = clean_interest(interest)

            # Insert the data into the 'students' table
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'INSERT INTO students (full_name, roll_number, email, gender, dob, city, interest, department, degree_title, subject, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (full_name, roll_number, email, gender, dob, city, interest, department, degree_title, subject, start_date, end_date)
            )
            mysql.connection.commit()

            cursor.close()
            flash("Student added successfully.")
        else:
            # Fetch the unique interests from the 'students' table
            interest_options = get_unique_interests()
            print(interest_options)
            return render_template('add_student.html', interest_options=interest_options)
    else:
        return redirect(url_for('login'))


def get_unique_interests():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT DISTINCT interest FROM students")
    interests = cursor.fetchall()
    cursor.close()

    # Extract and clean up interests
    clean_interests = [clean_interest(interest[0]) for interest in interests if interest[0]]

    return clean_interests


def clean_interest(interest):
    # Remove any non-alphabetic characters
    cleaned_interest = ''.join(char for char in interest if char.isalpha())
    return cleaned_interest


@app.route('/students_list')
def students_list():
    if 'loggedin' in session:
        # Fetch students list from the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        cursor.close()

        return render_template('students_list.html', students=students)
    else:

        return redirect(url_for('login'))

@app.route('/get_students')
def get_students():
    # Fetch students list from the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    cursor.close()

    return jsonify(students)


@app.route("/view", methods=['GET', 'POST'])
def view_student():
    if 'loggedin' in session:
        student_id = request.args.get('student_id')
        # Fetch student details from the database using the student_id
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM students WHERE std_id = %s', (student_id,))
        student = cursor.fetchone()
        cursor.close()

        print(student)

        return render_template('view_student.html', student=student)
    else:
        return redirect(url_for('login'))


@app.route("/edit_button_action", methods=['GET', 'POST'])
def edit_button_action():
    if 'loggedin' in session:
        if request.method == 'GET':
            student_id = request.args.get('student_id')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM students WHERE std_id = %s', (student_id,))
            student = cursor.fetchone()
            cursor.close()

            # Fetch the unique interests from the 'students' table
            interest_options = get_unique_interests()

            return render_template('update_student.html', student=student, interest_options=interest_options)
        elif request.method == 'POST':
            # Handle the form submission logic here
            full_name = request.form['full_name']
            roll_number = request.form['roll_number']
            email = request.form['email']
            gender = request.form['gender']
            dob = request.form['dob']
            city = request.form['city']
            interest = request.form['interest']
            custom_interest = request.form.get('custom_interest', None)
            department = request.form['department']
            degree_title = request.form['degree_title']
            subject = request.form['subject']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            student_id = request.form['std_id']

            # If the selected interest is "custom," use the custom interest value
            if interest == "custom" and custom_interest:
                # Use custom_interest if provided
                interest = custom_interest

            # Validate form data as needed

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""
                UPDATE students SET
                full_name=%s, roll_number=%s, email=%s, gender=%s, dob=%s,
                city=%s, interest=%s, department=%s, degree_title=%s, subject=%s,
                start_date=%s, end_date=%s
                WHERE std_id=%s
            """, (full_name, roll_number, email, gender, dob, city, interest, department, degree_title, subject,
                  start_date, end_date, student_id))

            mysql.connection.commit()
            cursor.close()

            flash("Student information updated successfully.", "success")

            return redirect(url_for('students_list'))
    else:
        return redirect(url_for('login'))

@app.route("/ajax_delete", methods=["POST", "GET"])
def ajax_delete():
    try:
        if 'loggedin' in session:
            student_id = request.args.get('student_id')
            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM students WHERE std_id = %s", (student_id,))
            mysql.connection.commit()
            cursor.close()
            response = {'status': 'success', 'message': 'Are you sure delete the student?'}

            return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
