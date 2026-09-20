import os
import json
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.db import search_products_for_chatbot, get_business_info, get_product_by_handle, get_db
from src.recommender import get_recommender

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INDEX_PATH = os.path.join(BASE_DIR, 'faiss_index.bin')
CHUNKS_PATH = os.path.join(BASE_DIR, 'faiss_chunks.json')

REFUSAL_MESSAGE = (
    "I don't know. This information isn't available in the business data. "
    "For specific inquiries, custom designs, or orders, please contact RoSin directly on WhatsApp at +91 8438990370."
)

class RAGEngine:
    def __init__(self):
        print("Loading RAG Engine...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            print(f"Loaded FAISS index with {self.index.ntotal} chunks.")
        else:
            self.index = None
            self.chunks = []
            print("Warning: FAISS index not found. Run build_faiss_index.py first.")

        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, title, handle FROM products")
            self.products = [(r['id'], r['title'], r['handle']) for r in c.fetchall()]
            conn.close()
        except Exception:
            self.products = []
        self.last_product_handle = 'pink-stone-bridal-bangles'
        self.last_products = []
        self.last_filters = {}
        self.last_query = ""

    def classify_intent(self, query):
        q = query.lower().strip()

        # 1. Strict Out-of-Domain Guard
        out_of_domain_phrases = [
            'capital of', 'weather', 'python', 'java', 'c++', 'write a program', 'write code',
            'president of', 'prime minister of', 'tell me a joke', 'write an essay',
            'who is elon', 'who is the king', 'recipe for', 'stock market', 'bitcoin', 'crypto',
            'translate', 'who won the world cup', 'cricket match', 'tell me a story', 'what is today',
            'bake a chocolate', 'bake a cake', 'bake'
        ]
        if any(p in q for p in out_of_domain_phrases):
            return 'unknown'

        # 2. Catalog Search Indicators
        catalog_indicators = [
            'under', 'below', 'less than', 'price', 'cost', '₹', 'rs', 'rupee', 'inr',
            '2.2', '2.4', '2.6', '2.8', '2.10', '2.12',
            'bangle', 'bangles', 'necklace', 'neckpieces', 'neckpiece', 'necklaces',
            'earring', 'earrings', 'stud', 'studs', 'choker', 'kada', 'kundan', 'bridal set',
            'claw', 'clip', 'saree pin', 'haaram', 'haram', 'kanti', 'jhumka', 'jhumkas', 'jhumki',
            'jadau', 'hipchain', 'waist chain', 'vaddanam', 'ottiyanam', 'combo', 'combos', 'set', 'sets',
            'chain', 'show me', 'show', 'recommend', 'buy', 'looking for', 'do you have',
            'scrunchie', 'scrunchies', 'glass bangles', 'first one', 'second one', 'third one',
            '2nd one', '1st one', 'size', 'sizes', 'product', 'products', 'items', 'item'
        ]

        # 3. Policy & FAQ Indicators
        policy_indicators = [
            'shipping', 'ship', 'delivery', 'deliver', 'canada', 'international',
            'courier', 'dispatch', 'return', 'returns', 'refund', 'refunds', 'exchange', 'damage', 'broken',
            'unboxing', 'custom', 'customize', 'customized', 'customise', 'customised', 'customization',
            'match', 'matching', 'saree photo', 'lehenga', 'outfit', 'dress',
            'rent', 'rental', 'rentals', 'hours', 'timing', 'open', 'close', 'store',
            'address', 'location', 'phone', 'contact', 'whatsapp', 'email',
            'founder', 'history', 'who started', 'who founded', 'care', 'water', 'wash',
            'payment', 'payments', 'pay', 'upi', 'cod', 'cash on delivery', 'urgent', 'express',
            'options', 'policy', 'about', 'how do i order', 'how to order', 'how can i contact'
        ]

        # 4. Recommendation Indicators
        recommendation_indicators = [
            'suggest', 'recommend', 'recommendation', 'recommendations',
            'similar to', 'more like this', 'similar product', 'something similar',
            'for a red saree', 'for a saree', 'for a wedding', 'for wedding', 'for a function',
            'for bride', 'wedding jewellery', 'wedding jewelry',
            'earrings to match', 'match my', 'match with',
            'affordable', 'elegant', 'something for', 'need jewellery for',
            'need jewelry for', 'need bangles for', 'want something', 'i want bridal'
        ]

        has_catalog = any(re.search(rf'\b{re.escape(w)}\b', q) for w in catalog_indicators)
        has_policy = any(re.search(rf'\b{re.escape(w)}\b', q) for w in policy_indicators)
        has_recommendation = any(re.search(rf'\b{re.escape(w)}\b', q) for w in recommendation_indicators)
        is_order_faq = any(q.startswith(p) for p in ['how do i', 'how to', 'what is', 'who is', 'who founded', 'can i', 'do you offer', 'what happens'])

        if has_recommendation and not is_order_faq:
            return 'recommendation'
        elif has_catalog and has_policy:
            if is_order_faq:
                return 'policy_faq'
            return 'hybrid'
        elif has_catalog:
            return 'catalog_search'
        elif has_policy:
            return 'policy_faq'
        else:
            return 'semantic_search'

    def retrieve_semantic(self, query, top_k=3):
        if not self.index or len(self.chunks) == 0:
            return []

        q_vec = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q_vec)

        scores, indices = self.index.search(q_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.chunks):
                results.append({
                    'score': float(score),
                    'chunk': self.chunks[idx]
                })
        return results

    def extract_catalog_filters(self, query):
        q = query.lower()
        filters = {
            'category': None,
            'subcategory': None,
            'max_price': None,
            'min_price': None,
            'size': None,
            'color': None,
            'availability': None,
            'keywords': []
        }

        # 1. Price extraction
        # Range / Between: "between ₹2000 and ₹5000", "2000 to 5000", "between 2000 and 5000"
        range_match = re.search(r'(?:between|from)?\s*(?:rs\.?|inr|₹)?\s*(\d+)\s*(?:to|and|-)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
        if range_match and any(w in q for w in ['between', 'to', 'and', 'from', '-']):
            p1 = float(range_match.group(1))
            p2 = float(range_match.group(2))
            if p1 > 0 and p2 > p1:
                filters['min_price'] = p1
                filters['max_price'] = p2

        # Min price: "above ₹3000", "more than 3000", "over 3000", "starting from 3000"
        if filters['min_price'] is None:
            min_match = re.search(r'(?:above|more than|greater than|over|starting from|min|minimum of)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
            if min_match:
                filters['min_price'] = float(min_match.group(1))

        # Max price: "under ₹2000", "below 2000", "less than ₹2000", "up to ₹2000", "within 2000", "budget of 2000"
        if filters['max_price'] is None:
            max_match = re.search(r'(?:under|below|less than|up to|within|max|budget of)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
            if max_match:
                filters['max_price'] = float(max_match.group(1))

        if filters['max_price'] is None:
            direct_price = re.search(r'(?:rs\.?|₹)\s*(\d+)', q)
            if direct_price and any(w in q for w in ['under', 'below', 'less', 'within', 'max']):
                filters['max_price'] = float(direct_price.group(1))

        # 2. Size extraction
        size_match = re.search(r'\b(2\.[2468]|2\.10|2\.12)\b', q) or re.search(r'\b(\d+\.\d+)\b', q)
        if size_match:
            filters['size'] = size_match.group(1)

        # 3. Color extraction
        color_candidates = ['green', 'red', 'pink', 'yellow', 'blue', 'purple', 'gold', 'golden', 'silver', 'maroon', 'white', 'black', 'orange', 'multi']
        for color in color_candidates:
            if re.search(rf'\b{color}\b', q):
                filters['color'] = 'gold' if color == 'golden' else color
                break

        # 4. Availability extraction
        if 'in stock' in q or 'available' in q:
            filters['availability'] = 'In Stock'

        # 5. Exact Category / Subcategory extraction
        if 'bridal full' in q or 'bridal full set' in q or 'bridal full sets' in q:
            filters['subcategory'] = 'Bridal Full Sets'
            filters['category'] = 'Jewellery'
        elif 'bridal combo' in q or 'bridal combo set' in q or 'bridal combo sets' in q:
            filters['subcategory'] = 'Bridal Combo Sets'
            filters['category'] = 'Jewellery'
        elif 'bridal jewel' in q or 'bridal jewellery' in q or 'bridal jewelry' in q:
            filters['subcategory'] = 'Bridal Jewellery'
            filters['category'] = 'Jewellery'
        elif 'bridal bangle' in q or 'bridal bangles' in q:
            filters['subcategory'] = 'Bridal Bangles'
            filters['category'] = 'Bangles'
        elif 'hipchain' in q or 'waist chain' in q or 'vaddanam' in q or 'ottiyanam' in q:
            filters['subcategory'] = 'Bridal Jewellery'
            filters['category'] = 'Jewellery'
        elif 'jhumka' in q or 'jhumkas' in q or 'jhumki' in q:
            filters['subcategory'] = 'Jhumkas'
            filters['category'] = 'Jewellery'
        elif 'earring' in q or 'earrings' in q or 'stud' in q or 'studs' in q or 'maatal' in q:
            filters['subcategory'] = 'Earrings'
            filters['category'] = 'Jewellery'
        elif 'necklace' in q or 'necklaces' in q or 'neckpiece' in q or 'neckpieces' in q or 'choker' in q or 'haaram' in q or 'haram' in q or 'kanti' in q:
            filters['subcategory'] = 'Necklaces'
            filters['category'] = 'Jewellery'
        elif 'combo box' in q or 'combo boxes' in q or 'bangle box' in q:
            filters['subcategory'] = 'Combo Boxes'
            filters['category'] = 'Bangles'
        elif 'glass bangle' in q or 'glass bangles' in q or 'glass' in q:
            filters['subcategory'] = 'Glass Bangles'
            filters['category'] = 'Bangles'
        elif 'kundan' in q:
            filters['subcategory'] = 'Budget Kundan Set'
            filters['category'] = 'Bangles'
        elif 'kada' in q:
            filters['subcategory'] = 'Broad Kada Bangles'
            filters['category'] = 'Bangles'
        elif 'ghungroo' in q or 'metal bangle' in q:
            filters['subcategory'] = 'Ghungroo & Metal Bangles'
            filters['category'] = 'Bangles'
        elif 'kid' in q or 'child' in q or 'children' in q:
            filters['subcategory'] = 'Kids Bangles'
            filters['category'] = 'Bangles'
        elif 'scrunchie' in q or 'scrunchies' in q or 'gajra' in q:
            filters['subcategory'] = 'Scrunchies'
            filters['category'] = 'Hair Accessories'
        elif 'hair clip' in q or 'hair clips' in q or 'claw' in q or 'claws' in q:
            filters['subcategory'] = 'Hair Clips'
            filters['category'] = 'Hair Accessories'
        elif 'bangle' in q or 'bangles' in q:
            filters['category'] = 'Bangles'
        elif 'jewel' in q or 'jewellery' in q or 'jewelry' in q:
            filters['category'] = 'Jewellery'
        elif 'hair' in q:
            filters['category'] = 'Hair Accessories'

        # 6. Stopwords & Meaningful Keywords
        stopwords = {
            'i', 'need', 'want', 'show', 'me', 'the', 'a', 'an', 'in', 'under', 'below',
            'for', 'have', 'you', 'do', 'any', 'bangles', 'bangle', 'set', 'size', 'sizes',
            'price', 'cost', 'available', 'products', 'product', 'item', 'items', 'please', 'tell',
            'find', 'which', 'what', 'does', 'come', 'comes', 'are', 'is', 'can', 'get', 'give',
            'look', 'looking', 'of', 'with', 'this', 'that', 'these', 'those', 'all', 'or', 'some',
            'jewellery', 'jewelry', 'between', 'above', 'more', 'less', 'than', 'to', 'and', 'from',
            'earrings', 'earring', 'jhumka', 'jhumkas', 'necklace', 'necklaces', 'bridal',
            'up', 'starting', 'min', 'max', 'budget'
        }
        if filters['color']:
            stopwords.add(filters['color'])
            if filters['color'] == 'gold':
                stopwords.add('golden')

        clean_q = re.sub(r'[^\w\s]', ' ', q)
        words = clean_q.split()
        meaningful_words = [
            w for w in words 
            if w not in stopwords and not re.match(r'^\d+(\.\d+)?$', w)
        ]
        if meaningful_words:
            filters['keywords'] = meaningful_words[:2]

        return filters

    def answer_query(self, query, product_handle=None):
        query = query.strip()
        if not query:
            return {
                'reply': "Please ask a question about RoSin's products, sizes, prices, or store policies.",
                'recommended_products': [],
                'citations': [],
                'intent': 'empty',
                'confidence_score': 0.0
            }

        q_lower = query.lower()

        # Update last product handle if provided
        if product_handle:
            self.last_product_handle = product_handle

        intent = self.classify_intent(query)

        # 0. STRICT OUT-OF-DOMAIN REFUSAL
        if intent == 'unknown':
            return {
                'reply': REFUSAL_MESSAGE,
                'recommended_products': [],
                'citations': [],
                'intent': 'unknown',
                'confidence_score': 0.0
            }

        # 1. CONVERSATIONAL ORDINAL FOLLOW-UP (e.g. "show the second one", "2nd one", "first one")
        ordinal_patterns = {
            'first': 0, '1st': 0,
            'second': 1, '2nd': 1,
            'third': 2, '3rd': 2,
            'fourth': 3, '4th': 3
        }
        matched_ordinal = None
        for word, idx in ordinal_patterns.items():
            if re.search(rf'\b{word}\b', q_lower):
                if any(w in q_lower for w in ['show', 'view', 'tell', 'details', 'one', 'item', 'product', 'the']):
                    matched_ordinal = idx
                    break

        if matched_ordinal is not None and hasattr(self, 'last_products') and self.last_products:
            if matched_ordinal < len(self.last_products):
                prod = self.last_products[matched_ordinal]
                self.last_product_handle = prod['handle']
                sizes_str = ', '.join(prod['sizes']) if prod.get('sizes') else 'Standard / Free size'
                reply = (
                    f"Here are the verified details for **{prod['title']}**:\n"
                    f"- **Price**: ₹{int(prod['price']):,}\n"
                    f"- **Category**: {prod.get('category', '')} → {prod.get('subcategory', '')}\n"
                    f"- **Availability**: {prod.get('availability', 'In Stock')}\n"
                    f"- **Available Sizes**: {sizes_str}\n\n"
                    f"You can view complete product details or add it directly to your cart below."
                )
                return {
                    'reply': reply,
                    'recommended_products': [prod],
                    'citations': ["RoSin Verified Product Database"],
                    'intent': 'catalog_search',
                    'confidence_score': 1.0
                }

        # 2. SIZE QUERY HANDLING
        has_size_word = any(w in q_lower for w in ['size', 'sizes', 'dimension', 'diameter'])
        size_number_match = re.search(r'\b(2\.[2468]|2\.10|2\.12)\b', q_lower) or re.search(r'\b(\d+\.\d+)\b', q_lower)
        is_size_query = has_size_word or bool(size_number_match)
        is_size_guide_faq = any(p in q_lower for p in ['how to measure', 'how do i check', 'how to check', 'size guide', 'measure your hand', 'sizing guide'])
        if is_size_guide_faq and not size_number_match:
            is_size_query = False

        # Target product detection for product-specific inquiries
        target_product = None
        if hasattr(self, 'products'):
            for pid, title, handle in self.products:
                t_clean = title.lower().rstrip('s')
                if (len(t_clean) > 4 and t_clean in q_lower) or handle in q_lower:
                    target_product = get_product_by_handle(handle)
                    break

        if not target_product:
            has_deictic = any(p in q_lower for p in ['this product', 'this bangle', 'this item', 'this set', 'these bangles', 'for this', 'does this', 'what sizes does this'])
            if has_deictic or product_handle:
                h = product_handle or getattr(self, 'last_product_handle', None)
                if h:
                    target_product = get_product_by_handle(h)

        if is_size_query:
            requested_size = size_number_match.group(1) if size_number_match else None

            # Case A: Product-specific size question
            if target_product and (has_size_word or requested_size):
                avail_sizes = target_product.get('sizes') or []
                self.last_product_handle = target_product['handle']

                if requested_size:
                    has_size = any(requested_size == s or f"{requested_size}(" in s or f"{requested_size} " in s for s in avail_sizes)
                    if has_size:
                        reply = f"Yes! {target_product['title']} is available in size {requested_size}. Verified available sizes for this item are: {', '.join(avail_sizes)}."
                    else:
                        sizes_str = ', '.join(avail_sizes) if avail_sizes else "None (standard one size)"
                        reply = f"No, size {requested_size} is not available for {target_product['title']}. Verified available sizes for this item are: {sizes_str}."
                else:
                    if avail_sizes:
                        reply = f"For {target_product['title']}, verified available sizes are: {', '.join(avail_sizes)}."
                    else:
                        reply = f"For {target_product['title']}, there are no size options; this handcrafted piece comes in a standard size with an adjustable back rope/chain."

                return {
                    'reply': reply,
                    'recommended_products': [target_product],
                    'citations': [target_product.get('source_url') or "RoSin Verified Product Catalog"],
                    'intent': 'catalog_search',
                    'confidence_score': 1.0
                }

            # Case B: Specific size requested across catalog (e.g. "Show bangles in size 2.6", "Do you have size 2.6?")
            if requested_size:
                category = 'Bangles'
                products = search_products_for_chatbot(category=category, size=requested_size, limit=4)
                if products:
                    self.last_products = products
                    self.last_filters = {'category': category, 'size': requested_size}
                    reply = f"Yes! Here are verified {category.lower()} available in size {requested_size} from RoSin's collection:"
                    return {
                        'reply': reply,
                        'recommended_products': products,
                        'citations': ["RoSin Verified Product Catalog"],
                        'intent': 'catalog_search',
                        'confidence_score': 1.0
                    }
                else:
                    reply = f"No products were found in RoSin's verified catalog available in size {requested_size}. Verified bangle sizes in our collection include: 2.2, 2.4, 2.6, 2.8, 2.10, and 2.12."
                    return {
                        'reply': reply,
                        'recommended_products': [],
                        'citations': ["RoSin Product Database"],
                        'intent': 'catalog_search',
                        'confidence_score': 0.8
                    }

            # Case C: General size inquiry following previous product search (e.g. "What sizes are available?")
            if hasattr(self, 'last_products') and self.last_products:
                all_sizes = list(dict.fromkeys(s for p in self.last_products for s in p.get('sizes', [])))
                last_label = self.last_filters.get('subcategory') or self.last_filters.get('category') or "these items"
                if all_sizes:
                    reply = f"For the {last_label} shown, verified available sizes are: {', '.join(all_sizes)}."
                else:
                    reply = f"For our {last_label} collection, each piece is handcrafted in a standard bridal size featuring an adjustable back rope (dori) or links for a comfortable fit."
                return {
                    'reply': reply,
                    'recommended_products': self.last_products[:2],
                    'citations': ["RoSin Verified Product Catalog"],
                    'intent': 'catalog_search',
                    'confidence_score': 1.0
                }

        # 2.5 RECOMMENDATION INTENT
        if intent == 'recommendation':
            rec = get_recommender().recommend_products(query, product_handle=getattr(self, 'last_product_handle', None), limit=4)
            if rec['success'] and rec['products']:
                self.last_products = rec['products']
                self.last_filters = rec['constraints']
                reply = rec['message']
                return {
                    'reply': reply,
                    'recommended_products': rec['products'],
                    'citations': ["RoSin Verified Product Catalog & AI Recommendation Engine"],
                    'intent': 'recommendation',
                    'confidence_score': rec['confidence_score']
                }
            else:
                reply = "I couldn't find a verified RoSin product matching those requirements. No verified products in RoSin's catalog match those criteria. Please try broadening your budget or exploring other styles."
                return {
                    'reply': reply,
                    'recommended_products': [],
                    'citations': ["RoSin Product Database"],
                    'intent': 'recommendation',
                    'confidence_score': 0.8
                }

        # 3. CATALOG SEARCH INTENT & CONVERSATIONAL FOLLOW-UPS
        if intent == 'catalog_search':
            filters = self.extract_catalog_filters(query)

            # Conversational follow-up: e.g. "Under ₹3000" or "below 2500" following earlier category search
            is_price_followup = (
                (filters['max_price'] is not None or filters['min_price'] is not None)
                and not filters['category']
                and not filters['subcategory']
                and not filters['keywords']
                and not any(w in q_lower for w in ['product', 'products', 'item', 'items', 'catalog', 'collection', 'everything'])
                and hasattr(self, 'last_filters')
                and bool(self.last_filters.get('category') or self.last_filters.get('subcategory'))
            )
            if is_price_followup:
                filters['category'] = self.last_filters.get('category')
                filters['subcategory'] = self.last_filters.get('subcategory')
                if not filters['size'] and self.last_filters.get('size'):
                    filters['size'] = self.last_filters.get('size')
                if not filters['color'] and self.last_filters.get('color'):
                    filters['color'] = self.last_filters.get('color')

            products = search_products_for_chatbot(
                category=filters['category'],
                subcategory=filters['subcategory'],
                max_price=filters['max_price'],
                min_price=filters['min_price'],
                size=filters['size'],
                color=filters['color'],
                availability=filters['availability'],
                keywords=filters['keywords'],
                limit=4
            )

            # Build human-readable criteria string
            criteria_desc = []
            if filters['subcategory']:
                criteria_desc.append(filters['subcategory'])
            elif filters['category']:
                criteria_desc.append(filters['category'])
            if filters['min_price'] and filters['max_price']:
                criteria_desc.append(f"between ₹{int(filters['min_price']):,} and ₹{int(filters['max_price']):,}")
            elif filters['max_price']:
                criteria_desc.append(f"under ₹{int(filters['max_price']):,}")
            elif filters['min_price']:
                criteria_desc.append(f"above ₹{int(filters['min_price']):,}")
            if filters['size']:
                criteria_desc.append(f"in size {filters['size']}")
            if filters['color']:
                criteria_desc.append(f"in {filters['color']}")

            crit_str = " ".join(criteria_desc) if criteria_desc else "matching products"

            if products:
                self.last_products = products
                self.last_filters = filters
                if not filters['subcategory'] and not filters['category']:
                    reply = f"Here are verified products {crit_str} from RoSin's collection:"
                else:
                    reply = f"Here are verified {crit_str} from RoSin's collection:"
                confidence_score = 1.0
                citations = ["RoSin Verified Product Catalog"]
            else:
                reply = f"I couldn't find a verified RoSin product matching those requirements. No verified products in RoSin's catalog match those criteria ({crit_str}). Please try relaxing your price range or exploring other categories."
                confidence_score = 0.8
                citations = ["RoSin Product Database"]

            return {
                'reply': reply,
                'recommended_products': products,
                'citations': citations,
                'intent': intent,
                'confidence_score': confidence_score
            }

        # 2. POLICY / FAQ / SEMANTIC INTENT
        semantic_matches = self.retrieve_semantic(query, top_k=3)
        top_match = semantic_matches[0] if semantic_matches else None

        is_verified_match = False
        if top_match:
            score = top_match['score']
            chunk = top_match['chunk']
            q_lower = query.lower()

            topical_keywords = {
                'shipping': ['ship', 'shipping', 'delivery', 'deliver', 'canada', 'international', 'dispatch', 'courier', 'days', 'urgent', 'express', 'options', 'timeline', 'track', 'tracking', 'order', 'orders'],
                'returns': ['return', 'returns', 'refund', 'refunds', 'exchange', 'damage', 'broken', 'unboxing', 'break', 'video'],
                'orders': ['custom', 'customize', 'customized', 'customise', 'customised', 'customization', 'saree', 'dress', 'outfit', 'match', 'matching', 'size', 'guide', 'measure', 'kid', 'kids', 'order', 'orders'],
                'services': ['rent', 'rental', 'rentals'],
                'business_info': ['hour', 'hours', 'time', 'timing', 'store', 'address', 'location', 'phone', 'contact', 'whatsapp', 'email', 'founder', 'who', 'sindhu', 'senthilkumar', 'about', 'owner', 'started', 'founded', 'brand', 'studio', 'artisan', 'artisans'],
                'payments': ['payment', 'pay', 'payments', 'method', 'methods', 'upi', 'card', 'cards', 'debit', 'credit', 'net banking', 'cod', 'cash on delivery', 'advance', 'accepted', 'options', 'gateway'],
                'general': ['founder', 'who', 'started', 'founded', 'about', 'story', 'heritage', 'sindhu', 'senthilkumar', 'rosin', 'craft', 'artisans', 'artisan', 'studio', 'faq', 'frequently', 'questions'],
                'care': ['water', 'wash', 'soap', 'gold', 'pure gold', '24k', 'material', 'care', 'clean', 'maintenance']
            }

            category = chunk.get('category', '')
            cat_keywords = topical_keywords.get(category, [])
            has_keyword_overlap = any(kw in q_lower for kw in cat_keywords)

            # Heuristic: Out-of-domain check for 24K gold or bullion requests
            if '24k' in q_lower or 'pure gold' in q_lower or 'gold biscuit' in q_lower or 'bullion' in q_lower:
                return {
                    'reply': "RoSin specializes exclusively in handmade silk-thread bangles, glass bangles, and fashion imitation jewellery. We do NOT sell 24K pure gold, gold biscuits, or precious bullion.",
                    'recommended_products': [],
                    'citations': ["RoSin Product Catalog & Business Policy"],
                    'intent': 'policy_faq',
                    'confidence_score': 0.95
                }

            if score >= 0.55 or (score >= 0.38 and has_keyword_overlap):
                is_verified_match = True

        if is_verified_match:
            recommended_products = []
            chunk = top_match['chunk']
            confidence_score = top_match['score']
            citations = [chunk['source_url']]
            content = chunk['content']

            if "Answer:" in content:
                ans_text = content.split("Answer:")[1].strip()
            else:
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('Business Name:') and not l.startswith('Source:') and not l.startswith('Verified Date:') and not l.startswith('Topic:') and not l.startswith('Question:')]
                ans_text = " ".join(lines)

            reply = ans_text

            if intent == 'hybrid':
                filters = self.extract_catalog_filters(query)
                products = search_products_for_chatbot(
                    category=filters['category'],
                    subcategory=filters['subcategory'],
                    max_price=filters['max_price'],
                    min_price=filters['min_price'],
                    size=filters['size'],
                    color=filters['color'],
                    availability=filters['availability'],
                    limit=2
                )
                if products:
                    recommended_products = products
                    reply += "\n\nHere are matching products from our catalog:"

            return {
                'reply': reply,
                'recommended_products': recommended_products,
                'citations': citations,
                'intent': 'policy_faq' if intent in ['policy_faq', 'semantic_search'] else intent,
                'confidence_score': round(confidence_score, 3)
            }

        # 3. OUT-OF-DOMAIN / UNANSWERABLE QUERY (STRICT REFUSAL)
        return {
            'reply': REFUSAL_MESSAGE,
            'recommended_products': [],
            'citations': [],
            'intent': 'unknown',
            'confidence_score': round(top_match['score'], 3) if top_match else 0.0
        }

_rag_instance = None
def get_rag():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance
