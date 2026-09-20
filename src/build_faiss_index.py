import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KB_DIR = os.path.join(BASE_DIR, 'data', 'knowledge_base')
INDEX_PATH = os.path.join(BASE_DIR, 'faiss_index.bin')
CHUNKS_PATH = os.path.join(BASE_DIR, 'faiss_chunks.json')

def build_index():
    print("Initializing embedding model: all-MiniLM-L6-v2...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    chunks = []

    # 1. Base files from knowledge_base
    meta_path = os.path.join(KB_DIR, 'chunks_metadata.json')
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata_list = json.load(f)
    meta_map = {m['file_name']: m for m in metadata_list}

    txt_files = [f for f in os.listdir(KB_DIR) if f.endswith('.txt')]
    for fname in txt_files:
        fpath = os.path.join(KB_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        meta = meta_map.get(fname, {
            'chunk_id': f'kb_{fname}',
            'document_type': 'general',
            'category': 'general',
            'topic': fname.replace('.txt', '').replace('_', ' ').title(),
            'source_url': 'https://rosinjewellery.com',
            'verified_date': '2026-09-18'
        })

        chunks.append({
            'chunk_id': meta['chunk_id'],
            'title': meta.get('topic', fname),
            'category': meta.get('category', 'general'),
            'document_type': meta.get('document_type', 'policy'),
            'content': content,
            'source_url': meta.get('source_url', 'https://rosinjewellery.com'),
            'verified_date': '2026-09-18'
        })

    # 2. Enhanced Targeted Chunks with explicit semantic query triggers
    chunks.append({
        'chunk_id': 'shipping_handmade_timeline',
        'title': 'Handmade Jewellery Crafting and Dispatch Timeline - How long does delivery take?',
        'category': 'shipping',
        'document_type': 'policy',
        'content': 'Question: How long does shipping and delivery take? Answer: All RoSin handmade jewellery items are made to order. It takes 7 to 10 business days for artisans to handcraft your jewellery before it is ready to ship. Domestic shipping within India takes 3 to 10 business days after dispatch. Total delivery time is approximately 10 to 20 days.',
        'source_url': 'https://rosinjewellery.com/pages/shipping-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'shipping_international_canada',
        'title': 'International Shipping - Do you deliver to Canada, USA, UK, worldwide?',
        'category': 'shipping',
        'document_type': 'policy',
        'content': 'Question: Do you deliver to Canada, USA, UK, Australia, or internationally? Answer: Yes, RoSin provides international shipping worldwide. Delivery takes 1 to 2 weeks. All international orders must be placed directly by contacting WhatsApp at +91 8438990370 or Instagram DM @rosin_bangles. Customs fees, duties, and taxes are the responsibility of the customer.',
        'source_url': 'https://rosinjewellery.com/pages/shipping-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'shipping_urgent_express',
        'title': 'Urgent Orders and Express Shipping Dispatch',
        'category': 'shipping',
        'document_type': 'policy',
        'content': 'Question: Do you have express shipping or immediate dispatch for urgent orders? Answer: Yes we do. For urgent orders or immediate dispatch, kindly contact RoSin via WhatsApp at +91 8438990370.',
        'source_url': 'https://rosinjewellery.com/pages/shipping-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'return_refund_exchange_policy',
        'title': 'Return Policy, Refund, and Size Exchange Rules',
        'category': 'returns',
        'document_type': 'policy',
        'content': 'Question: What is your return policy? Can I return, refund, or exchange? Answer: All RoSin jewellery items are custom made on order. RoSin strictly does not provide exchange, return, or refund. Size exchange is not provided; customers must check the size guide before ordering.',
        'source_url': 'https://rosinjewellery.com/pages/return-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'transit_damage_unboxing_video',
        'title': 'Damage in Transit, Broken Bangles, and Mandatory Unboxing Video',
        'category': 'returns',
        'document_type': 'policy',
        'content': 'Question: What happens if my bangles are broken or damaged in transit? Answer: In case of damage during transit, contact RoSin via WhatsApp at +91 8438990370 within 2 days of delivery with an uncut, continuous 360-degree unboxing video displaying all sides before opening. For glass bangles, breakage of 1 or 2 bangles is normal transit wear and beyond control; claims are reviewed only if more than 6 bangles are broken.',
        'source_url': 'https://rosinjewellery.com/pages/return-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'custom_outfit_matching_saree',
        'title': 'Customizing Bangles for Saree, Lehenga, or Bridal Outfits',
        'category': 'orders',
        'document_type': 'faq',
        'content': 'Question: How do I order a customised set to match my saree or outfit? Answer: All our sets can be customized matching your outfits. Kindly DM us on Instagram @rosin_bangles or WhatsApp us at +91 8438990370. Send us your outfit picture and the model you like. After payment and confirmation we will craft and dispatch it.',
        'source_url': 'https://rosinjewellery.com/pages/faqs',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'bangle_size_guide_standards',
        'title': 'Bangle Size Guide, Measurements, and Kids Sizes',
        'category': 'orders',
        'document_type': 'faq',
        'content': 'Question: How do I check my bangle size? Are kids sizes available? Answer: Size 2.4 has an inner diameter of 6.0 cm. Size 2.6 has an inner diameter of 6.3 to 6.5 cm. Size 2.8 has an inner diameter of 6.7 cm. Measure your hand or an existing bangle before ordering. Kids sizes are also available under the Kids collection.',
        'source_url': 'https://rosinjewellery.com/pages/faqs',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'rental_jewellery_service',
        'title': 'Imitation Jewellery Rental Service',
        'category': 'services',
        'document_type': 'faq',
        'content': 'Question: Do you have imitation jewellery for rent? Answer: Yes, RoSin provides bridal imitation jewellery for rent. Visit our physical store directly in Pallipalayam or contact us on WhatsApp at +91 8438990370 for rental details.',
        'source_url': 'https://rosinjewellery.com/pages/faqs',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'store_location_hours_contact',
        'title': 'Store Opening Hours, Physical Location, and Contact Details',
        'category': 'business_info',
        'document_type': 'business_info',
        'content': 'Question: What are your store opening hours, location, and contact number? Answer: Rosin Bridal Jewels store is located at RS Road, opposite to SK Consulting, Erode - Pallipalayam Rd, Pallipalayam, Tamil Nadu 638006. Opening Hours: Everyday 9:00 AM - 6:00 PM IST. WhatsApp & Phone: +91 8438990370. Email: rosinfashionjewellery@gmail.com.',
        'source_url': 'https://rosinjewellery.com/pages/contact',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'product_material_care',
        'title': 'Product Materials, Imitation Jewellery, and Water Care',
        'category': 'care',
        'document_type': 'policy',
        'content': 'Question: What materials are used? Are they waterproof? Answer: RoSin specializes in handmade silk thread bangles, glass bangles, imitation jewellery, and fashion hair accessories. We do NOT sell real fine 24K/22K gold or precious bullion. The delicate bangles are not for daily rough wear and should not be used with soap or water; remove while bathing or washing.',
        'source_url': 'https://rosinjewellery.com/pages/return-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'shipping_options_dispatch',
        'title': 'Shipping Options, Delivery Timeline, and Dispatch Methods',
        'category': 'shipping',
        'document_type': 'policy',
        'content': 'Question: What are the shipping options? How do you ship orders? Answer: RoSin provides domestic shipping across India (3 to 10 business days after crafting) and international shipping worldwide (1 to 2 weeks). For urgent orders, express courier dispatch is available upon request via WhatsApp at +91 8438990370. All handmade jewellery requires 7 to 10 business days to handcraft before dispatch.',
        'source_url': 'https://rosinjewellery.com/pages/shipping-policy',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'business_founder_heritage',
        'title': 'Founder of RoSin, Artisan Heritage, and Women-Led Studio',
        'category': 'business_info',
        'document_type': 'business_info',
        'content': 'Question: Who is the founder of RoSin? Who founded RoSin Jewellery? Answer: RoSin Bangles & Jewellery was founded in 2021 by Sindhu Senthilkumar as a woman-led craft studio in Pallipalayam, Tamil Nadu. RoSin is dedicated to empowering local women artisans who handcraft traditional silk-thread bangles, bridal jewellery sets, and fashion accessories.',
        'source_url': 'https://rosinjewellery.com/pages/about-us',
        'verified_date': '2026-09-18'
    })

    chunks.append({
        'chunk_id': 'accepted_payment_methods',
        'title': 'Accepted Payment Methods, Online Checkout, UPI, and Advance Payment',
        'category': 'payments',
        'document_type': 'policy',
        'content': 'Question: What payment methods are accepted? What payment options do you accept? Answer: RoSin accepts all major online payment options including UPI (Google Pay, PhonePe, Paytm), credit cards, debit cards, and net banking via secure online checkout. For custom orders on WhatsApp or Instagram, direct UPI and bank transfers are accepted. Cash on Delivery (COD) is not accepted because all items are customized and made to order.',
        'source_url': 'https://rosinjewellery.com/pages/faqs',
        'verified_date': '2026-09-18'
    })

    print(f"Total knowledge chunks to embed: {len(chunks)}")

    texts = [f"{c['title']}\n{c['content']}" for c in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True)

    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Re-built FAISS Index at {INDEX_PATH} with {index.ntotal} vectors.")

if __name__ == '__main__':
    build_index()
