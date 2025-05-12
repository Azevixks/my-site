from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://azevixks.github.io/"])

@app.route('/')
def home():
    return "Welcome to the Teachable Machine Image Model API!"

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    class_name = data.get('class_name')

    prices = get_supermarket_prices_filtered(class_name)
    if prices:
        return jsonify({
            'class_name': class_name,
            'results': prices
        })
    else:
        return jsonify({'error': 'Товар не знайдено'}), 404


def get_supermarket_prices_filtered(class_name=None):
    url = 'https://index.minfin.com.ua/ua/markets/wares/prods/fruits-vegetables/vegetables/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    result = {}
    if not class_name:
        return None  # Потрібна назва товару

    normalized_name = class_name.lower()
    result[normalized_name] = {}

    prods_div = soup.find("div", class_="prodsviewshop")
    if not prods_div:
        return None

    rows = prods_div.find_all("tr")
    current_market = None

    for row in rows:
        th = row.find("th")
        if th and th.has_attr("colspan"):
            current_market = th.text.strip()
        elif row.find("td") and current_market:
            cells = row.find_all("td")
            if len(cells) == 3 and cells[2].find("big") and cells[2].find("small"):
                product_name = cells[0].text.strip().lower()
                if normalized_name in product_name:
                    price_uah = cells[2].find("big").text.strip().replace(',', '.').split(".")[0]
                    price_kop = cells[2].find("small").text.strip()
                    full_price = float(f"{price_uah}.{price_kop}")

                    result[normalized_name][current_market] = round(full_price, 2)

    return result if result[normalized_name] else None


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port)