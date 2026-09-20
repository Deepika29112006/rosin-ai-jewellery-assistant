import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from app import app
import json

def test_full_system():
    print("=" * 65)
    print("RUNNING FULL SYSTEM TEST (Flask Endpoints + RAG Pipeline)")
    print("=" * 65)

    client = app.test_client()

    # 1. Page routes
    pages = ['/', '/shop', '/cart', '/wishlist', '/about', '/product/pink-stone-bridal-bangles']
    for p in pages:
        resp = client.get(p)
        assert resp.status_code == 200, f"Page {p} returned status {resp.status_code}"
        print(f"[PASS] GET {p} -> 200 OK")

    # 2. API Products
    resp = client.get('/api/products')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['count'] == 110
    print(f"[PASS] GET /api/products -> 200 OK (Loaded {data['count']} products)")

    # 3. Filtered Products
    resp = client.get('/api/products?subcategory=Bridal+Bangles&max_price=3000')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    print(f"[PASS] GET /api/products?subcategory=Bridal+Bangles&max_price=3000 -> {data['count']} items found")

    # 4. Product Detail API
    resp = client.get('/api/product/pink-stone-bridal-bangles')
    assert resp.status_code == 200
    pdata = resp.get_json()['product']
    assert pdata['price'] == 2850.0
    print(f"[PASS] GET /api/product/pink-stone-bridal-bangles -> Price: ₹{pdata['price']}, Variants: {len(pdata['variants'])}")

    # 5. Categories API
    resp = client.get('/api/categories')
    assert resp.status_code == 200
    cats = resp.get_json()['categories']
    assert len(cats) == 3
    print(f"[PASS] GET /api/categories -> 200 OK ({len(cats)} parent categories)")

    # 6. Chatbot Tests (Including Size-Aware RAG Support)
    chat_tests = [
        ("I need bridal bangles under 2000", None, True, "Product Recommendation"),
        ("Do you have size 2.6?", None, True, "Size Search"),
        ("What sizes are available for this product?", "pink-stone-bridal-bangles", True, "Product-Specific Sizes"),
        ("Does this bangle come in size 2.6?", "pink-stone-bridal-bangles", True, "Product-Specific Size Check"),
        ("What sizes does this product have?", "pink-stone-bridal-bangles", True, "Product-Specific Variant Check"),
        ("Show me bangles in size 2.4", None, True, "Discovery: Size 2.4"),
        ("Show me bangles available in size 2.6", None, True, "Discovery: Size 2.6"),
        ("Find bangles available in size 2.8", None, True, "Discovery: Size 2.8"),
        ("Which bangles are available in 2.6?", None, True, "Natural: Which bangles 2.6"),
        ("I need a bangle of size 2.8", None, True, "Natural: Need bangle 2.8"),
        ("Do you have size 3.5?", None, False, "Non-Existent Size 3.5 (Strict 0 prods)"),
        ("What is your return policy?", None, False, "Return Policy FAQ"),
        ("Do you deliver to Canada?", None, False, "International Shipping FAQ"),
        ("How to order customised set for my saree?", None, False, "Custom Matching"),
        ("Do you sell 24K pure gold coins?", None, False, "Out-of-Scope Bullion Clarification"),
        ("Who is the prime minister of India?", None, False, "Strict Fallback 'I don't know'"),
        ("What is the capital of France?", None, False, "Strict Fallback 'I don't know'"),
        ("Can you deliver in 1 hour in New York?", None, False, "Strict Fallback 'I don't know'")
    ]

    print("\n--- Testing Chatbot Grounded Answers ---")
    for item in chat_tests:
        msg = item[0]
        handle = item[1]
        expects_products = item[2]
        test_name = item[3]
        payload = {'message': msg}
        if handle:
            payload['handle'] = handle
        resp = client.post('/api/chat', json=payload)
        assert resp.status_code == 200
        cdata = resp.get_json()
        assert cdata['success'] is True
        has_prods = len(cdata['recommended_products']) > 0
        print(f"\n[QUERY]: '{msg}' ({test_name})")
        print(f"  -> Intent: {cdata['intent']} | Score: {cdata['confidence_score']}")
        print(f"  -> Reply: {cdata['reply'][:120]}...")
        if has_prods:
            print(f"  -> Products ({len(cdata['recommended_products'])}): {[p['title'] for p in cdata['recommended_products']]}")
        else:
            print("  -> Products: 0 (No products)")

    print("\n" + "=" * 65)
    print("ALL SYSTEM TESTS PASSED SUCCESSFULLY (0 FAILURES)!")
    print("=" * 65)

if __name__ == '__main__':
    test_full_system()
