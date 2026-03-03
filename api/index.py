# api/index.py

# -------------------------------
# 1️⃣ Suppress Warnings (optional)
# -------------------------------
import warnings
warnings.filterwarnings("ignore")  # hides sklearn warnings temporarily

# -------------------------------
# 2️⃣ Import Libraries
# -------------------------------
from flask import Flask, render_template, request, jsonify
from utils.crop_engine import CropEngine

# -------------------------------
# 3️⃣ Initialize Flask App
# -------------------------------
app = Flask(__name__)
crop_engine = CropEngine()  # your custom model engine

# -------------------------------
# 4️⃣ Define Routes
# -------------------------------
@app.route('/')
def home():
    return render_template('index.html')  # your homepage

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        prediction = crop_engine.predict(data)  # adjust based on your CropEngine
        return jsonify({'prediction': prediction})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -------------------------------
# 5️⃣ Run the App
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)