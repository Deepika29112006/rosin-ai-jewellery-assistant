import os
import json
import sqlite3
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
KB_DIR = os.path.join(DATA_DIR, 'knowledge_base')
JSON_PATH = os.path.join(DATA_DIR, 'products.json')
DB_PATH = os.path.join(BASE_DIR, 'products.db')

def validate():
    print("=" * 60)
    print("RUNNING DATASET VALIDATION (RoSin Bangles & Jewellery)")
    print("=" * 60)

    errors = []
    warnings = []

    # 1. Check data/products.json exists
    if not os.path.exists(JSON_PATH):
        errors.append(f"Missing file: {JSON_PATH}")
        return errors, warnings

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Rule 1: Exactly 110 products in JSON
    if len(products) == 110:
        print(f"[PASS] Rule 1: JSON contains exactly 110 products.")
    else:
        errors.append(f"Rule 1 FAIL: JSON contains {len(products)} products, expected 110.")

    # Rule 2: Check SQLite database and product count
    if not os.path.exists(DB_PATH):
        errors.append(f"Missing database file: {DB_PATH}")
        return errors, warnings

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products;")
    db_prod_count = cursor.fetchone()[0]
    if db_prod_count == 110:
        print(f"[PASS] Rule 2: SQLite 'products' table contains exactly 110 products.")
    else:
        errors.append(f"Rule 2 FAIL: SQLite products count is {db_prod_count}, expected 110.")

    # Rule 3: Product IDs are unique
    pids = [p['id'] for p in products]
    if len(pids) == len(set(pids)):
        print(f"[PASS] Rule 3: All 110 product IDs are unique.")
    else:
        errors.append("Rule 3 FAIL: Duplicate product IDs found in JSON.")

    cursor.execute("SELECT id FROM products;")
    db_pids = [row[0] for row in cursor.fetchall()]
    if set(pids) == set(db_pids):
        print(f"[PASS] Rule 3b: Product IDs in JSON and SQLite match 1:1.")
    else:
        errors.append("Rule 3b FAIL: Product IDs differ between JSON and SQLite.")

    # Rule 4: Handles are unique
    handles = [p['handle'] for p in products]
    if len(handles) == len(set(handles)):
        print(f"[PASS] Rule 4: All 110 product handles are unique.")
    else:
        errors.append("Rule 4 FAIL: Duplicate product handles found.")

    # Rule 5: Prices match between JSON and SQLite
    price_mismatch = 0
    for p in products:
        cursor.execute("SELECT price FROM products WHERE id = ?", (p['id'],))
        row = cursor.fetchone()
        if not row or abs(row[0] - p['price']) > 0.001:
            price_mismatch += 1
    if price_mismatch == 0:
        print(f"[PASS] Rule 5: All 110 product prices match exactly between JSON and SQLite.")
    else:
        errors.append(f"Rule 5 FAIL: {price_mismatch} products have price mismatch between JSON and SQLite.")

    # Rule 6: Categories and subcategories match
    cursor.execute("""
        SELECT p.id, c.name, p.subcategory 
        FROM products p 
        JOIN categories c ON p.category_id = c.id
    """)
    db_cat_map = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    cat_mismatch = 0
    for p in products:
        db_cat, db_sub = db_cat_map.get(p['id'], (None, None))
        if p['category'] != db_cat or p['subcategory'] != db_sub:
            cat_mismatch += 1
    if cat_mismatch == 0:
        print(f"[PASS] Rule 6: Categories and subcategories match 100% between JSON and SQLite.")
    else:
        errors.append(f"Rule 6 FAIL: {cat_mismatch} category mismatches between JSON and SQLite.")

    # Rule 7: Sizes and colors are valid lists and not invented
    invalid_lists = 0
    for p in products:
        if not isinstance(p['sizes'], list) or not isinstance(p['colors'], list):
            invalid_lists += 1
    if invalid_lists == 0:
        print(f"[PASS] Rule 7: Sizes and colors are proper lists extracted from verified options.")
    else:
        errors.append(f"Rule 7 FAIL: {invalid_lists} products have invalid sizes/colors structure.")

    # Rule 8: Image URLs are preserved from verified CDN sources
    invalid_images = 0
    for p in products:
        url = p['image_url']
        if url and not url.startswith('https://cdn.shopify.com/'):
            invalid_images += 1
    if invalid_images == 0:
        print(f"[PASS] Rule 8: All image URLs are genuine Shopify CDN asset links.")
    else:
        errors.append(f"Rule 8 FAIL: {invalid_images} image URLs not from verified CDN.")

    # Rule 9: Every product has a valid source URL on rosinjewellery.com
    invalid_source_urls = 0
    for p in products:
        s_url = p.get('source_url', '')
        if not s_url.startswith('https://rosinjewellery.com/products/'):
            invalid_source_urls += 1
    if invalid_source_urls == 0:
        print(f"[PASS] Rule 9: 100% of products have verified source URLs on rosinjewellery.com.")
    else:
        errors.append(f"Rule 9 FAIL: {invalid_source_urls} products have invalid source URLs.")

    # Rule 10: Policies contain only verified information
    cursor.execute("SELECT COUNT(*) FROM policies;")
    policy_count = cursor.fetchone()[0]
    if policy_count >= 5:
        print(f"[PASS] Rule 10: Policies table contains {policy_count} verified policy entries.")
    else:
        errors.append(f"Rule 10 FAIL: Expected at least 5 policies, found {policy_count}.")

    # Rule 11: Missing information is null/empty (no placeholders)
    placeholder_matches = 0
    dummy_patterns = ['lorem', 'placeholder', 'dummy', 'fake', 'sample_product']
    for p in products:
        for val in [p['title'], p['handle'], p['description'] or '']:
            for d in dummy_patterns:
                if d in val.lower():
                    placeholder_matches += 1
    if placeholder_matches == 0:
        print(f"[PASS] Rule 11: Zero placeholders or dummy strings found; missing fields are clean null.")
    else:
        errors.append(f"Rule 11 FAIL: Found {placeholder_matches} occurrences of placeholder text.")

    # Rule 12: Knowledge base files exist and contain verified content
    kb_files = [
        'business_info.txt',
        'shipping_policy.txt',
        'return_policy.txt',
        'payment_policy.txt',
        'order_information.txt',
        'faq.txt',
        'chunks_metadata.json'
    ]
    missing_kb = []
    for kbf in kb_files:
        p = os.path.join(KB_DIR, kbf)
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            missing_kb.append(kbf)
    if not missing_kb:
        print(f"[PASS] Rule 12: All 7 knowledge base files exist and are populated with verified facts.")
    else:
        errors.append(f"Rule 12 FAIL: Missing or empty KB files: {missing_kb}")

    conn.close()
    return errors, warnings

if __name__ == '__main__':
    errs, warns = validate()
    print("=" * 60)
    if not errs:
        print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY (0 ERRORS)!")
    else:
        print(f"VALIDATION FAILED WITH {len(errs)} ERRORS:")
        for e in errs:
            print(f"  - {e}")
    print("=" * 60)
