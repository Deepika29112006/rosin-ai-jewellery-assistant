import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'products.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_products(category=None, subcategory=None, size=None, color=None, availability=None, min_price=None, max_price=None, query=None, sort='featured'):
    conn = get_db()
    cursor = conn.cursor()

    sql = """
    SELECT DISTINCT p.id, p.title, p.handle, p.price, p.subcategory, p.description,
           p.availability, p.source_url, c.name as category_name,
           (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY image_order ASC LIMIT 1) as image_url
    FROM products p
    JOIN categories c ON p.category_id = c.id
    LEFT JOIN product_variants pv ON p.id = pv.product_id
    WHERE 1=1
    """
    params = []

    if category:
        sql += " AND c.name = ?"
        params.append(category)

    if subcategory:
        sql += " AND p.subcategory = ?"
        params.append(subcategory)

    if min_price is not None:
        sql += " AND p.price >= ?"
        params.append(float(min_price))

    if max_price is not None:
        sql += " AND p.price <= ?"
        params.append(float(max_price))

    if size:
        sql += " AND pv.size LIKE ?"
        params.append(f"%{size}%")

    if color:
        sql += " AND pv.color LIKE ?"
        params.append(f"%{color}%")

    if availability:
        sql += " AND p.availability = ?"
        params.append(availability)

    if query:
        sql += " AND (p.title LIKE ? OR p.subcategory LIKE ? OR p.description LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term])

    # Sorting
    if sort == 'price_asc':
        sql += " ORDER BY p.price ASC"
    elif sort == 'price_desc':
        sql += " ORDER BY p.price DESC"
    elif sort == 'name':
        sql += " ORDER BY p.title ASC"
    else:
        sql += " ORDER BY p.id ASC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    products = []
    for r in rows:
        pid = r['id']
        # Fetch sizes
        c_sizes = conn.cursor()
        c_sizes.execute("SELECT DISTINCT size FROM product_variants WHERE product_id = ? AND size IS NOT NULL", (pid,))
        sizes = [s['size'] for s in c_sizes.fetchall()]

        # Fetch colors
        c_colors = conn.cursor()
        c_colors.execute("SELECT DISTINCT color FROM product_variants WHERE product_id = ? AND color IS NOT NULL", (pid,))
        colors = [cl['color'] for cl in c_colors.fetchall()]

        products.append({
            'id': r['id'],
            'title': r['title'],
            'handle': r['handle'],
            'price': float(r['price']),
            'category': r['category_name'],
            'subcategory': r['subcategory'],
            'description': r['description'],
            'sizes': sizes,
            'colors': colors,
            'availability': r['availability'],
            'image_url': r['image_url'],
            'source_url': r['source_url']
        })

    conn.close()
    return products

def get_product_by_handle(handle):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.title, p.handle, p.price, p.subcategory, p.description,
               p.availability, p.source_url, p.verified_date, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.handle = ?
    """, (handle,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    pid = row['id']

    # Images
    cursor.execute("SELECT image_url FROM product_images WHERE product_id = ? ORDER BY image_order ASC", (pid,))
    images = [img['image_url'] for img in cursor.fetchall()]

    # Variants
    cursor.execute("SELECT size, color, price, availability FROM product_variants WHERE product_id = ?", (pid,))
    variants = [
        {
            'size': v['size'],
            'color': v['color'],
            'price': float(v['price']),
            'availability': v['availability']
        }
        for v in cursor.fetchall()
    ]

    # Distinct sizes
    sizes = list(dict.fromkeys(v['size'] for v in variants if v['size']))
    # Distinct colors
    colors = list(dict.fromkeys(v['color'] for v in variants if v['color']))

    product = {
        'id': row['id'],
        'title': row['title'],
        'handle': row['handle'],
        'price': float(row['price']),
        'category': row['category_name'],
        'subcategory': row['subcategory'],
        'description': row['description'],
        'sizes': sizes,
        'colors': colors,
        'availability': row['availability'],
        'source_url': row['source_url'],
        'verified_date': row['verified_date'],
        'images': images,
        'variants': variants
    }

    conn.close()
    return product

def get_categories_tree():
    conn = get_db()
    cursor = conn.cursor()

    def count_query(cat_name, subcat_name):
        cursor.execute(
            "SELECT COUNT(*) FROM products p JOIN categories c ON p.category_id = c.id WHERE c.name = ? AND p.subcategory = ?",
            (cat_name, subcat_name)
        )
        return cursor.fetchone()[0]

    result = [
        {
            'id': 1,
            'name': 'Bangles',
            'handle': 'bangles',
            'subcategories': [
                {'name': 'Bridal Bangles', 'handle': 'bridal-bangles', 'count': count_query('Bangles', 'Bridal Bangles')},
                {'name': 'Combo Boxes', 'handle': 'combo-boxes', 'count': count_query('Bangles', 'Combo Boxes')},
                {'name': 'Broad Kada Bangles', 'handle': 'broad-kada-bangles', 'count': count_query('Bangles', 'Broad Kada Bangles')},
                {'name': 'Glass Bangles', 'handle': 'glass-bangles', 'count': count_query('Bangles', 'Glass Bangles')},
                {'name': 'Budget Kundan Set', 'handle': 'budget-kundhan-mixed-set', 'count': count_query('Bangles', 'Budget Kundan Set')},
                {'name': 'Ghungroo & Metal Bangles', 'handle': 'ghungroo-and-metal', 'count': count_query('Bangles', 'Ghungroo & Metal Bangles')},
                {'name': 'Kids Bangles', 'handle': 'kids', 'count': count_query('Bangles', 'Kids Bangles')}
            ]
        },
        {
            'id': 2,
            'name': 'Jewellery',
            'handle': 'jewellery',
            'subcategories': [
                {'name': 'Necklaces', 'handle': 'necklaces', 'count': count_query('Jewellery', 'Necklaces')},
                {'name': 'Earrings', 'handle': 'earrings', 'count': count_query('Jewellery', 'Earrings')},
                {'name': 'Jhumkas', 'handle': 'jhumkas', 'count': count_query('Jewellery', 'Jhumkas')},
                {'name': 'Bridal Full Sets', 'handle': 'bridal-full-sets', 'count': count_query('Jewellery', 'Bridal Full Sets')},
                {'name': 'Bridal Combo Sets', 'handle': 'bridal-combo-sets', 'count': count_query('Jewellery', 'Bridal Combo Sets')},
                {'name': 'Bridal Jewellery', 'handle': 'bridal-jewellery', 'count': count_query('Jewellery', 'Bridal Jewellery')}
            ]
        },
        {
            'id': 3,
            'name': 'Hair Accessories',
            'handle': 'hair-accessories',
            'subcategories': [
                {'name': 'Scrunchies', 'handle': 'scrunchies', 'count': count_query('Hair Accessories', 'Scrunchies')},
                {'name': 'Hair Clips', 'handle': 'hair-clips', 'count': count_query('Hair Accessories', 'Hair Clips')}
            ]
        }
    ]

    conn.close()
    return result

def get_business_info():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM business_info")
    info = {r['key']: r['value'] for r in cursor.fetchall()}
    conn.close()
    return info

def get_policies():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT policy_type, title, content, source_url, verified_date FROM policies")
    policies = {
        r['policy_type']: {
            'title': r['title'],
            'content': r['content'],
            'source_url': r['source_url'],
            'verified_date': r['verified_date']
        }
        for r in cursor.fetchall()
    }
    conn.close()
    return policies

def search_products_for_chatbot(category=None, subcategory=None, max_price=None, min_price=None, size=None, color=None, availability=None, keywords=None, limit=4):
    conn = get_db()
    cursor = conn.cursor()

    sql = """
    SELECT DISTINCT p.id, p.title, p.handle, p.price, p.subcategory, p.availability, c.name as category_name,
           (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY image_order ASC LIMIT 1) as image_url
    FROM products p
    JOIN categories c ON p.category_id = c.id
    LEFT JOIN product_variants pv ON p.id = pv.product_id
    WHERE 1=1
    """
    params = []

    if category:
        sql += " AND c.name LIKE ?"
        params.append(f"%{category}%")

    if subcategory:
        sql += " AND p.subcategory LIKE ?"
        params.append(f"%{subcategory}%")

    if max_price is not None:
        sql += " AND p.price <= ?"
        params.append(float(max_price))

    if min_price is not None:
        sql += " AND p.price >= ?"
        params.append(float(min_price))

    if size:
        sql += " AND pv.size LIKE ?"
        params.append(f"%{size}%")

    if color:
        sql += " AND (pv.color LIKE ? OR p.title LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{color}%", f"%{color}%", f"%{color}%"])

    if availability:
        sql += " AND p.availability LIKE ?"
        params.append(f"%{availability}%")

    if keywords:
        kw_clauses = []
        for kw in keywords:
            kw_clauses.append("(p.title LIKE ? OR p.subcategory LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])
        if kw_clauses:
            sql += " AND (" + " OR ".join(kw_clauses) + ")"

    sql += " ORDER BY p.price ASC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        pid = r['id']
        c_sizes = conn.cursor()
        c_sizes.execute("SELECT DISTINCT size FROM product_variants WHERE product_id = ? AND size IS NOT NULL", (pid,))
        sizes = [s['size'] for s in c_sizes.fetchall()]

        results.append({
            'id': r['id'],
            'title': r['title'],
            'handle': r['handle'],
            'price': float(r['price']),
            'category': r['category_name'],
            'subcategory': r['subcategory'],
            'availability': r['availability'] or 'In Stock',
            'sizes': sizes,
            'image_url': r['image_url'],
            'source_url': f"https://rosinjewellery.com/products/{r['handle']}"
        })

    conn.close()
    return results
