# RoSin — AI-Powered Bangles & Jewellery Shopping Assistant

**Hackathon Product Prototype for a Real Local Business**
- **Business Name:** RoSin Bangles / RoSin Jewellery / RoSin Bridal Jewels
- **Founder:** Sindhu Senthilkumar (Founded 2021)
- **Physical Outlet:** RS Road, opp. SK Consulting, Erode - Pallipalayam Rd, Pallipalayam, Tamil Nadu 638006
- **WhatsApp / Phone:** `+91 8438990370`
- **Instagram:** `@rosin_bangles`
- **Official Website:** `rosinjewellery.com`

---

## 💎 Project Highlights & Zero-Hallucination RAG

1. **100% Real Business Data:** Exactly 110 verified real products with live Shopify CDN images, authentic prices (₹45 to ₹3,350), and real sizes (`2.2`, `2.4`, `2.6`, `2.8`, `Kids`).
2. **Dual-Retrieval Architecture:**
   - **Catalog Inquiries:** Handled by a deterministic SQL engine on `products.db` for price, size, and category matching.
   - **Store Policies & FAQs:** Handled by a FAISS semantic vector index (`all-MiniLM-L6-v2`) over verified RoSin policy documents.
3. **Strict Zero-Hallucination Guardrail:**
   - Any query outside verified business knowledge triggers:
     > *"I don't know. This information isn't available in the business data. For specific inquiries, custom designs, or orders, please contact RoSin directly on WhatsApp at +91 8438990370."*
4. **Seamless WhatsApp Order Flow:**
   - Interactive cart generates pre-filled WhatsApp checkout messages with item names, selected sizes, quantities, and totals directly to RoSin's verified number (`+91 8438990370`).

---

## 📁 Project Structure

```
Roshin_bangles&jewellery/
├── app.py                             # Flask application router & API endpoints
├── products.db                        # SQLite relational database (6 tables)
├── faiss_index.bin                    # FAISS vector store (all-MiniLM-L6-v2)
├── faiss_chunks.json                  # Chunks metadata and ground truth text
├── requirements.txt                   # Core Python dependencies
├── data/
│   ├── products.json                  # Master dataset of 110 verified products
│   └── knowledge_base/                # Factual business policy documents
│       ├── business_info.txt
│       ├── shipping_policy.txt
│       ├── return_policy.txt
│       ├── payment_policy.txt
│       ├── order_information.txt
│       ├── faq.txt
│       └── chunks_metadata.json
├── src/
│   ├── db.py                          # Parameterized SQLite query engine
│   ├── rag_engine.py                  # Dual-Retrieval RAG engine & confidence gate
│   ├── build_faiss_index.py           # FAISS index builder script
│   ├── validate_dataset.py            # 12-rule dataset validation test suite
│   └── test_system.py                 # Full end-to-end integration test suite
├── static/
│   ├── css/
│   │   ├── main.css                   # Modern luxury jewellery e-commerce stylesheet
│   │   └── chatbot.css                # Floating AI Assistant widget & recommendation cards
│   └── js/
│       ├── main.js                    # Cart state management (localStorage)
│       ├── catalog.js                 # Multi-facet filters, price slider, size pills
│       ├── product.js                 # Dynamic image gallery & variant selectors
│       ├── cart.js                    # Cart table & WhatsApp order generator
│       └── chatbot.js                 # AI Assistant UI & message streaming
└── templates/
    ├── index.html                     # Home page
    ├── shop.html                      # Catalogue page
    ├── product.html                   # Product details page
    ├── cart.html                      # Shopping cart page
    └── about.html                     # About Us & verified policy hub
```

---

## 🚀 Installation & Running Guide (Windows / PowerShell)

### 1. Navigate to Project Directory
```powershell
cd C:\Users\uppud\OneDrive\Desktop\Roshin_bangles&jewellery
```

### 2. Install Required Dependencies
All dependencies are standard, lightweight, and free (no GPU required):
```powershell
py -m pip install -r requirements.txt
```

### 3. Run Automated Validation & Integrity Tests
Run the 12-rule dataset integrity test:
```powershell
py src/validate_dataset.py
```
Run the full system end-to-end test suite (Flask APIs + RAG pipeline):
```powershell
py src/test_system.py
```

### 4. Start the Application Server
```powershell
py app.py
```
Open your browser and visit:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Demo Test Queries for Hackathon Judges

Try asking the **RoSin AI Assistant** (floating button at bottom-right):

1. **Product Recommendation by Budget:**
   > *"I need bridal bangles under ₹2000"*
   *(Returns real matching sets: Gold lakshmi border bangles, Traditional red muhurtham set, etc.)*
2. **Specific Bangle Size:**
   > *"Do you have size 2.6?"*
   *(Identifies size 2.6 variants from verified inventory)*
3. **Return Policy Inquiry:**
   > *"What is your return policy?"*
   *(Explains the strict made-to-order no-return policy and unboxing video requirement)*
4. **International Shipping:**
   > *"Do you deliver to Canada?"*
   *(Explains worldwide international shipping takes 1 to 2 weeks via WhatsApp orders)*
5. **Custom Matching:**
   > *"How to order customised set for my saree?"*
   *(Explains the outfit photo matching procedure)*
6. **Bullion / Gold Inquiry:**
   > *"Do you sell 24K pure gold coins?"*
   *(Clarifies RoSin specializes in silk-thread, glass, and imitation jewellery)*
7. **Strict Unanswerable Test:**
   > *"Who is the prime minister of India?"*
   *(Accurately refuses with zero hallucination: "I don't know. This information isn't available in the business data...")*

---

## 💼 Business Pitch: Pitching RoSin as a Paying Client

1. **The Problem RoSin Faces Today:**
   - RoSin receives hundreds of Instagram DMs and WhatsApp inquiries asking repetitive questions: *"What sizes are available in this set?"*, *"Do you ship to US/Canada?"*, *"Can you customize for my saree?"*, *"What is the return policy?"*.
   - Manual replies take hours, losing prospective bridal customers during peak seasons.
2. **The RoSin AI Solution:**
   - 24/7 instant shopping assistant integrated into their storefront.
   - Converts casual inquiries into structured WhatsApp orders (`wa.me/918438990370`) with prefilled product names and sizes.
   - Guaranteed **zero hallucinations** protecting RoSin's brand reputation.
3. **The Commercial Pitch:**
   - *"We built this prototype specifically for RoSin using your live catalog. It automates 80% of your pre-order sizing and policy inquiries, letting your artisan team focus on crafting."*
