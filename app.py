from flask import Flask, request, jsonify, redirect # <-- Added redirect here
import secrets
import re

app = Flask(__name__)

# Temporary In-memory database
url_database = {}

def get_url_mapping(short_code):
    """Abstraction layer for reading data."""
    # TODAY: Look up in dictionary
    return url_database.get(short_code)
    
    # TOMORROW: Your code will look like this:
    # mapping = URLMapping.query.filter_by(short_code=short_code).first()
    # return mapping.original_url if mapping else None


@app.route('/<short_code>', methods=['GET'])
def redirect_to_url(short_code):
    # 1. Fetch the original URL using our abstraction layer
    original_url = get_url_mapping(short_code)
    
    # 2. Handle missing codes
    if not original_url:
        return jsonify({"error": "Short code not found"}), 404
        
    # 3. Perform a 302 Found (temporary) redirect
    return redirect(original_url)


# --- Keep your existing /shorten route below ---
@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing required field: url"}), 400
    
    original_url = data['url']
    short_code = secrets.token_urlsafe(6)[:6]
    
    # Save to our temporary DB
    url_database[short_code] = original_url
    
    return jsonify({
        "short_code": short_code,
        "original_url": original_url
    }), 201

if __name__ == '__main__':
    app.run(debug=True)
