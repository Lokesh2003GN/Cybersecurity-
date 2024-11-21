from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
import sqlite3, os
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize database
def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, 
                       name TEXT, 
                       email TEXT, 
                       phone TEXT, 
                       password TEXT,
                       percentage_charging INTEGER,  
                       latitude REAL,
                       longitude REAL,
                       cookies TEXT,
                       image_filename TEXT)''')  # Store only the image filename
    conn.commit()
    conn.close()

# Call init_db() to ensure the table is created
init_db()

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')  # Serve the HTML form

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')  # Store plain-text password
        percentage_charging = int(request.form.get('percentage_charging', 0))
        latitude = float(request.form.get('latitude', 0.0)) if request.form.get('latitude') else None
        longitude = float(request.form.get('longitude', 0.0)) if request.form.get('longitude') else None
        cookies = request.form.get('cookies', None)

        # Handle image upload
        image = request.files.get('image')
        image_filename = None

        if image and allowed_file(image.filename):
            # Set image filename as the username
            image_filename = secure_filename(f"{name}.jpg")
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Basic validation
        if not name or not email or not phone or not password:
            return jsonify({"error": "Name, email, phone, and password are required fields."}), 400

        # Save to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users 
                          (name, email, phone, password, percentage_charging, latitude, longitude, cookies, image_filename) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (name, email, phone, password, percentage_charging, latitude, longitude, cookies, image_filename))
        conn.commit()
        conn.close()

        return jsonify({"message": "Data saved successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/show-data')
def show_data():
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        conn.close()

        # Render the HTML page to display the data
        return render_template('show_data.html', users=users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<int:user_id>', methods=['POST'])
def delete_data(user_id):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Retrieve the image filename before deleting the record
        cursor.execute("SELECT image_filename FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], result[0])
            if os.path.exists(image_path):
                os.remove(image_path)

        # Delete the user record
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('show_data'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
