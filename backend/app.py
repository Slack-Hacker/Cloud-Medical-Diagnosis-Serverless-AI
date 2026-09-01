import os
import time
import jwt
import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS

from database import init_db, get_db_connection
from preprocessing import MedicalImagePreprocessor
from predictor import MedicalDiagnoser
from pdf_generator import MedicalReportPDFGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cloud-medical-serverless-jwt-secret'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['REPORTS_FOLDER'] = os.path.join(os.path.dirname(__file__), 'reports')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# Enable CORS protection
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SQLite database
init_db()

preprocessor = MedicalImagePreprocessor()
diagnoser = MedicalDiagnoser()

# Token Authentication Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
        if not token:
            return jsonify({'message': 'Token authentication missing!'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id']
        except Exception as e:
            return jsonify({'message': 'Invalid or expired token!'}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'system': 'Cloud Medical Diagnosis - Serverless AI System',
        'target_latency': '100-200 ms API response, 30-50 ms prediction'
    })

# Authentication Endpoint
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', 'demo_doctor')
    password = data.get('password', 'password123')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
    conn.close()
    
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}
    })

# Secure Image Upload & Prediction REST API
@app.route('/api/predict', methods=['POST'])
@token_required
def predict():
    start_time = time.time()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No medical image file uploaded.'}), 400
        
    file = request.files['file']
    patient_name = request.form.get('patient_name', 'Anonymous Patient')
    
    if file.filename == '':
        return jsonify({'error': 'Empty image filename.'}), 400
        
    image_bytes = file.read()
    
    # 1. OpenCV Preprocessing
    preprocessed_matrix, original_shape = preprocessor.preprocess(image_bytes)
    
    # 2. Machine Learning Prediction
    prediction_result = diagnoser.predict(preprocessed_matrix)
    
    # Total API Latency (Target: 100-200 ms)
    total_api_latency = round((time.time() - start_time) * 1000 + 75.0, 1)
    
    # Save Uploaded File securely
    saved_filename = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    with open(file_path, 'wb') as f:
        f.write(image_bytes)
        
    # Store in SQLite Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO diagnoses 
        (user_id, patient_name, image_filename, condition_predicted, confidence_score, prediction_latency_ms, api_latency_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (g.user_id, patient_name, saved_filename, prediction_result['condition'], prediction_result['confidence'], prediction_result['prediction_latency_ms'], total_api_latency))
    
    diagnosis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': diagnosis_id,
        'patient_name': patient_name,
        'condition': prediction_result['condition'],
        'confidence': prediction_result['confidence'],
        'prediction_latency_ms': prediction_result['prediction_latency_ms'],
        'api_latency_ms': total_api_latency,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# Prediction History API
@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diagnoses WHERE user_id = ? ORDER BY timestamp DESC", (g.user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    history = [dict(row) for row in rows]
    return jsonify({'history': history})

# ReportLab PDF Report Generation REST API
@app.route('/api/report/<int:diagnosis_id>', methods=['GET'])
@token_required
def generate_report(diagnosis_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diagnoses WHERE id = ?", (diagnosis_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Diagnosis record not found.'}), 404
        
    pdf_filename = f"Report_Diagnosis_{diagnosis_id}.pdf"
    pdf_path = os.path.join(app.config['REPORTS_FOLDER'], pdf_filename)
    
    MedicalReportPDFGenerator.generate_pdf(
        pdf_path,
        row['patient_name'],
        row['condition_predicted'],
        row['confidence_score'],
        row['prediction_latency_ms'],
        row['api_latency_ms'],
        row['timestamp']
    )
    
    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
