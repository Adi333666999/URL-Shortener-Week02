from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
import secrets
import re
import os

app = Flask(__name__)

# Configure PostgreSQL Connection String
# Format: postgresql://username:password@hostname:port/database_name
# Change these values to match your PostgreSQL setup credentials
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "url_shortener")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the Database Instance
db = SQLAlchemy(app)

# ----------------------------------------------------
# DATABASE SCHEMA / MODEL
# ----------------------------------------------------
class URLMapping(db.Model):
    __tablename__ = 'url_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, short_code, original_url):
        self.short_code = short_code
        self.original_url = original_url

# Helper function to validate URLs
def is_valid_url(url):
    regex = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing required field: url"}), 400
    
    original_url = data['url']
    if not is_valid_url(original_url):
        return jsonify({"error": "Invalid URL format. Must start with http:// or https://"}), 422
    
    # Generate unique short code
    short_code = secrets.token_urlsafe(6)[:6]
    
    # Check for unexpected collisions in PostgreSQL
    while URLMapping.query.filter_by(short_code=short_code).first():
        short_code = secrets.token_urlsafe(6)[:6]
        
    # Database Transaction
    try:
        new_mapping = URLMapping(short_code=short_code, original_url=original_url)
        db.session.add(new_mapping)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database storage error occurred"}), 500
    
    return jsonify({
        "short_code": short_code,
        "original_url": original_url
    }), 201

@app.route('/<short_code>', methods=['GET'])
def redirect_to_url(short_code):
    # Fetch from PostgreSQL table
    mapping = URLMapping.query.filter_by(short_code=short_code).first()
    
    if not mapping:
        return jsonify({"error": "Short code not found"}), 404
        
    return redirect(mapping.original_url)

# Automatically create the database tables on startup
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
