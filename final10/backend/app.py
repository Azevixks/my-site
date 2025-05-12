from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Teachable Machine Image Model API!"

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    class_name = data.get('class_name')

    if class_name:
        # Fetch the price of the product based on the class name
        url = 'https://index.minfin.com.ua/ua/markets/wares/prods/fruits-vegetables/vegetables/'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.select_one('.price')  # Adjust the selector based on the actual HTML structure

        if price_element:
            price = price_element.text.strip()
            return jsonify({'class_name': class_name, 'price': price})
        else:
            return jsonify({'error': 'Price not found'}), 404
    else:
        return jsonify({'error': 'No class name provided'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)