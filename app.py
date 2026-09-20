import os
import sys
from flask import Flask, render_template, request, jsonify

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from src.db import (
    get_all_products,
    get_product_by_handle,
    get_categories_tree,
    get_business_info,
    get_policies
)
from src.rag_engine import get_rag
from src.recommender import get_recommender

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Lazy RAG Engine Initialization (preserves fast production startup)
rag_engine = None

def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = get_rag()
    return rag_engine

# ---------------------------------------------------------
# PAGE ROUTES (Frontend Views)
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/product/<handle>')
def product_page(handle):
    prod = get_product_by_handle(handle)
    if not prod:
        return render_template('shop.html', error=f"Product '{handle}' not found.")
    return render_template('product.html', handle=handle)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')

@app.route('/about')
def about():
    return render_template('about.html')

# ---------------------------------------------------------
# REST API ROUTES
# ---------------------------------------------------------

@app.route('/api/products', methods=['GET'])
def api_products():
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        size = request.args.get('size')
        color = request.args.get('color')
        availability = request.args.get('availability')
        query = request.args.get('query')
        sort = request.args.get('sort', 'featured')

        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')

        if min_price is not None and min_price != '':
            min_price = float(min_price)
        else:
            min_price = None

        if max_price is not None and max_price != '':
            max_price = float(max_price)
        else:
            max_price = None

        products = get_all_products(
            category=category,
            subcategory=subcategory,
            size=size,
            color=color,
            availability=availability,
            min_price=min_price,
            max_price=max_price,
            query=query,
            sort=sort
        )

        return jsonify({
            'success': True,
            'count': len(products),
            'products': products
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/product/<handle>', methods=['GET'])
def api_product_detail(handle):
    try:
        prod = get_product_by_handle(handle)
        if not prod:
            return jsonify({
                'success': False,
                'error': f"Product with handle '{handle}' not found."
            }), 404
        return jsonify({
            'success': True,
            'product': prod
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/product/<handle>/similar', methods=['GET'])
def api_product_similar(handle):
    try:
        limit = request.args.get('limit', 6, type=int)
        similar = get_recommender().get_similar_products(handle, limit=limit)
        return jsonify({
            'success': True,
            'count': len(similar),
            'products': similar
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def api_categories():
    try:
        categories = get_categories_tree()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business-info', methods=['GET'])
def api_business_info():
    try:
        info = get_business_info()
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/policies', methods=['GET'])
def api_policies():
    try:
        policies = get_policies()
        return jsonify({
            'success': True,
            'policies': policies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': "JSON payload must include a 'message' field."
            }), 400

        user_message = str(data['message']).strip()
        if not user_message:
            return jsonify({
                'success': False,
                'error': "Message cannot be empty."
            }), 400

        # Safety length limit
        if len(user_message) > 300:
            user_message = user_message[:300]

        # Optional product context for product-specific size inquiries
        handle = data.get('handle') or data.get('product_handle')

        # Process through grounded RAG Engine
        response = get_rag_engine().answer_query(user_message, product_handle=handle)

        return jsonify({
            'success': True,
            'reply': response['reply'],
            'intent': response['intent'],
            'recommended_products': response['recommended_products'],
            'citations': response['citations'],
            'confidence_score': response['confidence_score']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Internal chat processing error: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("RoSin Bangles & Jewellery E-Commerce & AI Assistant Server")
    print(f"Running on: http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
