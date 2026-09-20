import os
import re
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'products.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ProductRecommender:
    def __init__(self):
        print("Initializing ProductRecommender...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._load_products()

    def _load_products(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.title, p.handle, p.price, p.subcategory, p.availability, p.description,
                   c.name as category_name,
                   (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY image_order ASC LIMIT 1) as image_url
            FROM products p
            JOIN categories c ON p.category_id = c.id
        """)
        rows = c.fetchall()

        self.products = []
        texts_to_embed = []
        for r in rows:
            pid = r['id']
            # Fetch sizes and colors
            c_vars = conn.cursor()
            c_vars.execute("SELECT DISTINCT size, color FROM product_variants WHERE product_id = ?", (pid,))
            var_rows = c_vars.fetchall()
            sizes = list(dict.fromkeys(v['size'] for v in var_rows if v['size']))
            colors = list(dict.fromkeys(v['color'].lower() for v in var_rows if v['color']))

            prod_dict = {
                'id': r['id'],
                'title': r['title'],
                'handle': r['handle'],
                'price': float(r['price']),
                'category': r['category_name'],
                'subcategory': r['subcategory'],
                'availability': r['availability'] or 'In Stock',
                'description': r['description'] or '',
                'sizes': sizes,
                'colors': colors,
                'image_url': r['image_url'],
                'source_url': f"https://rosinjewellery.com/products/{r['handle']}"
            }
            self.products.append(prod_dict)

            # Text representation for embedding
            color_str = " ".join(colors) if colors else ""
            desc_clean = r['description'] or ''
            text = f"{r['title']} {r['category_name']} {r['subcategory']} {color_str} Rs.{int(r['price'])} {desc_clean}"
            texts_to_embed.append(text)

        conn.close()

        # Compute embeddings for all 110 products
        self.embeddings = self.model.encode(texts_to_embed, normalize_embeddings=True, convert_to_numpy=True)
        self.handle_to_idx = {p['handle']: idx for idx, p in enumerate(self.products)}
        print(f"ProductRecommender ready with {len(self.products)} products and embeddings.")

    def extract_recommendation_constraints(self, query):
        q = query.lower().strip()
        constraints = {
            'category': None,
            'subcategory': None,
            'max_price': None,
            'min_price': None,
            'color': None,
            'occasion': None,
            'style': None,
            'product_type': None,
            'is_similarity_request': False
        }

        # 1. Similarity trigger
        if any(p in q for p in ['similar to this', 'more like this', 'similar product', 'similar items', 'something similar', 'like this']):
            constraints['is_similarity_request'] = True

        # 2. Occasions
        occasion_map = {
            'wedding': 'wedding',
            'marriage': 'wedding',
            'bridal': 'bridal',
            'bride': 'bridal',
            'function': 'function',
            'party': 'party',
            'festival': 'festival',
            'festive': 'festival',
            'diwali': 'festival',
            'pongal': 'festival',
            'engagement': 'engagement',
            'daily': 'daily'
        }
        for occ, std in occasion_map.items():
            if re.search(rf'\b{occ}\b', q):
                constraints['occasion'] = std
                break

        # 3. Styles
        style_keywords = ['traditional', 'antique', 'kundan', 'lac', 'victorian', 'jadau', 'ghungroo', 'choker', 'haaram', 'kada', 'elegant', 'minimal']
        for st in style_keywords:
            if re.search(rf'\b{st}\b', q):
                constraints['style'] = st
                break

        # 4. Colors
        colors = ['red', 'green', 'pink', 'yellow', 'blue', 'gold', 'golden', 'silver', 'maroon', 'white', 'black', 'orange', 'multi', 'ruby', 'emerald']
        for col in colors:
            if re.search(rf'\b{col}\b', q):
                constraints['color'] = 'gold' if col == 'golden' else ('red' if col == 'ruby' else ('green' if col == 'emerald' else col))
                break

        # 5. Product types & Categories/Subcategories
        if re.search(r'\b(bridal full set|bridal full sets)\b', q):
            constraints['subcategory'] = 'Bridal Full Sets'
            constraints['category'] = 'Jewellery'
        elif re.search(r'\b(bridal combo set|bridal combo sets)\b', q):
            constraints['subcategory'] = 'Bridal Combo Sets'
            constraints['category'] = 'Jewellery'
        elif re.search(r'\b(bridal jewellery|bridal jewelry)\b', q):
            constraints['subcategory'] = 'Bridal Jewellery'
            constraints['category'] = 'Jewellery'
        elif re.search(r'\b(bridal bangle|bridal bangles)\b', q):
            constraints['subcategory'] = 'Bridal Bangles'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(glass bangle|glass bangles)\b', q):
            constraints['subcategory'] = 'Glass Bangles'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(combo box|combo boxes)\b', q):
            constraints['subcategory'] = 'Combo Boxes'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(broad kada|kada bangles|kada)\b', q):
            constraints['subcategory'] = 'Broad Kada Bangles'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(budget kundan|kundan set|kundan sets)\b', q):
            constraints['subcategory'] = 'Budget Kundan Set'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(ghungroo|metal bangles)\b', q):
            constraints['subcategory'] = 'Ghungroo & Metal Bangles'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(kids bangles|kid bangles)\b', q):
            constraints['subcategory'] = 'Kids Bangles'
            constraints['category'] = 'Bangles'
        elif re.search(r'\b(earring|earrings|stud|studs|maatal)\b', q):
            constraints['subcategory'] = 'Earrings'
            constraints['category'] = 'Jewellery'
            constraints['product_type'] = 'earrings'
        elif re.search(r'\b(jhumka|jhumkas|jhumki)\b', q):
            constraints['subcategory'] = 'Jhumkas'
            constraints['category'] = 'Jewellery'
            constraints['product_type'] = 'jhumkas'
        elif re.search(r'\b(necklace|necklaces|neckpiece|choker|haaram|haram|kanti)\b', q):
            constraints['subcategory'] = 'Necklaces'
            constraints['category'] = 'Jewellery'
            constraints['product_type'] = 'necklaces'
        elif re.search(r'\b(scrunchie|scrunchies|gajra)\b', q):
            constraints['subcategory'] = 'Scrunchies'
            constraints['category'] = 'Hair Accessories'
        elif re.search(r'\b(hair clip|hair clips|claw|claws)\b', q):
            constraints['subcategory'] = 'Hair Clips'
            constraints['category'] = 'Hair Accessories'
        elif re.search(r'\b(bangle|bangles)\b', q):
            constraints['category'] = 'Bangles'
            constraints['product_type'] = 'bangles'
        elif re.search(r'\b(jewel|jewellery|jewelry)\b', q):
            constraints['category'] = 'Jewellery'
            constraints['product_type'] = 'jewellery'
        elif re.search(r'\b(hair|hair accessories)\b', q):
            constraints['category'] = 'Hair Accessories'

        # Special phrasing: "earrings to match my necklace" -> target product type is earrings
        if 'earrings to match' in q or 'earring to match' in q or 'suggest earrings' in q:
            constraints['subcategory'] = 'Earrings'
            constraints['category'] = 'Jewellery'
            constraints['product_type'] = 'earrings'

        # 6. Price & Budget extraction
        # "between 2000 and 5000"
        range_match = re.search(r'(?:between|from)?\s*(?:rs\.?|inr|₹)?\s*(\d+)\s*(?:to|and|-)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
        if range_match and any(w in q for w in ['between', 'to', 'and', 'from', '-']):
            p1 = float(range_match.group(1))
            p2 = float(range_match.group(2))
            if p1 > 0 and p2 > p1:
                constraints['min_price'] = p1
                constraints['max_price'] = p2

        # "under 3000", "below 3000", "less than 3000", "within 3000"
        if constraints['max_price'] is None:
            max_match = re.search(r'(?:under|below|less than|within|up to|budget of|max)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
            if max_match:
                constraints['max_price'] = float(max_match.group(1))

        # "above 5000", "more than 5000"
        if constraints['min_price'] is None:
            min_match = re.search(r'(?:above|more than|greater than|over|starting from|min)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
            if min_match:
                constraints['min_price'] = float(min_match.group(1))

        # Qualitative budget keywords
        if 'affordable' in q or 'budget' in q or 'cheap' in q or 'pocket friendly' in q:
            if constraints['max_price'] is None:
                constraints['max_price'] = 1500.0

        if 'premium' in q or 'luxury' in q or 'heavy' in q:
            if constraints['min_price'] is None:
                constraints['min_price'] = 2500.0

        return constraints

    def recommend_products(self, query, product_handle=None, limit=4):
        constraints = self.extract_recommendation_constraints(query)

        # 1. Similarity to current/active product
        if constraints['is_similarity_request']:
            target_handle = product_handle or 'pink-stone-bridal-bangles'
            similar_items = self.get_similar_products(target_handle, limit=limit)
            if similar_items:
                return {
                    'success': True,
                    'products': similar_items,
                    'constraints': constraints,
                    'ranking_signal': 'semantic_product_similarity',
                    'confidence_score': 0.95,
                    'message': "Here are some verified RoSin products that match your request:"
                }
            else:
                return {
                    'success': False,
                    'products': [],
                    'constraints': constraints,
                    'ranking_signal': 'none',
                    'confidence_score': 0.8,
                    'message': "I couldn't find a verified RoSin product matching those requirements."
                }

        # 2. Hard constraint filtering from verified database
        candidates = []
        for idx, p in enumerate(self.products):
            # Category filter
            if constraints['category']:
                if constraints['category'].lower() not in p['category'].lower():
                    continue

            # Subcategory filter
            if constraints['subcategory']:
                if constraints['subcategory'].lower() not in p['subcategory'].lower():
                    # If looking for earrings, also accept Jhumkas
                    if constraints['subcategory'] == 'Earrings' and p['subcategory'] == 'Jhumkas':
                        pass
                    # If looking for Bridal Jewellery, also accept Bridal Full Sets or Bridal Combo Sets
                    elif constraints['subcategory'] == 'Bridal Jewellery' and ('Bridal' in p['subcategory']):
                        pass
                    else:
                        continue

            # Hard Max price filter
            if constraints['max_price'] is not None:
                if p['price'] > constraints['max_price']:
                    continue

            # Hard Min price filter
            if constraints['min_price'] is not None:
                if p['price'] < constraints['min_price']:
                    continue

            # Hard Color filter if explicit color required (e.g. "red saree" -> product must contain red)
            if constraints['color']:
                req_col = constraints['color'].lower()
                has_col = (
                    any(req_col in c.lower() for c in p['colors']) or
                    req_col in p['title'].lower() or
                    req_col in p['description'].lower()
                )
                if not has_col:
                    continue

            candidates.append((idx, p))

        # Strict Grounding: If 0 candidates satisfy constraints, refuse without silent relaxation
        if not candidates:
            return {
                'success': False,
                'products': [],
                'constraints': constraints,
                'ranking_signal': 'hard_constraint_filtering',
                'confidence_score': 0.8,
                'message': "I couldn't find a verified RoSin product matching those requirements."
            }

        # 3. Transparent Multi-Signal Ranking
        # Compute query embedding
        q_emb = self.model.encode(query, normalize_embeddings=True, convert_to_numpy=True)

        scored_candidates = []
        for idx, p in candidates:
            p_emb = self.embeddings[idx]
            semantic_sim = float(np.dot(p_emb, q_emb))  # [-1, 1] cosine similarity

            # Signal 1: Semantic relevance (weight 0.40)
            score = 0.40 * max(semantic_sim, 0.0)

            # Signal 2: Subcategory / Occasion alignment (weight 0.30)
            if constraints['occasion'] in ['wedding', 'bridal'] and 'Bridal' in p['subcategory']:
                score += 0.30
            elif constraints['occasion'] == 'festival' and ('Kundan' in p['subcategory'] or 'Bangles' in p['category']):
                score += 0.20
            elif constraints['style'] and (constraints['style'] in p['title'].lower() or constraints['style'] in p['description'].lower() or constraints['style'] in p['subcategory'].lower()):
                score += 0.25
            elif constraints['subcategory'] and constraints['subcategory'].lower() == p['subcategory'].lower():
                score += 0.25

            # Signal 3: Price / Budget fit (weight 0.15)
            if constraints['max_price']:
                # Favor products comfortably within budget rather than strictly at the limit
                budget_ratio = p['price'] / constraints['max_price']
                score += 0.15 * (1.0 - abs(0.7 - budget_ratio))
            else:
                score += 0.10

            # Signal 4: Color match bonus (weight 0.15)
            if constraints['color']:
                score += 0.15

            scored_candidates.append({
                'product': p,
                'score': round(score, 3),
                'semantic_similarity': round(semantic_sim, 3)
            })

        # Sort by total score descending
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        top_products = [sc['product'] for sc in scored_candidates[:limit]]

        return {
            'success': True,
            'products': top_products,
            'constraints': constraints,
            'ranking_signal': 'multi_signal_relevance',
            'confidence_score': round(scored_candidates[0]['score'], 3) if scored_candidates else 0.9,
            'message': "Here are some verified RoSin products that match your request:"
        }

    def get_similar_products(self, handle, limit=6):
        if handle not in self.handle_to_idx:
            return []

        target_idx = self.handle_to_idx[handle]
        target_p = self.products[target_idx]
        target_emb = self.embeddings[target_idx]

        scored_items = []
        for idx, p in enumerate(self.products):
            if idx == target_idx:
                continue

            p_emb = self.embeddings[idx]
            semantic_sim = float(np.dot(p_emb, target_emb))

            # Ranking signals for product similarity:
            # 1. Semantic description/title embedding (0.45)
            score = 0.45 * max(semantic_sim, 0.0)

            # 2. Subcategory exact match (0.35) or Category match (0.15)
            if p['subcategory'] == target_p['subcategory']:
                score += 0.35
            elif p['category'] == target_p['category']:
                score += 0.15

            # 3. Price closeness (0.20)
            max_ref = max(target_p['price'], 1000.0)
            price_diff = abs(p['price'] - target_p['price']) / max_ref
            score += 0.20 * max(0.0, 1.0 - price_diff)

            scored_items.append({
                'product': p,
                'score': round(score, 3)
            })

        scored_items.sort(key=lambda x: x['score'], reverse=True)
        return [item['product'] for item in scored_items[:limit]]

_recommender_instance = None

def get_recommender():
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = ProductRecommender()
    return _recommender_instance
