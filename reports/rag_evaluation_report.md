# RoSin AI Shopping Assistant - RAG Evaluation Report

**Evaluation Timestamp:** `2026-09-20T20:16:55.986149`  
**Target System:** `RoSin AI Shopping Assistant (RAGEngine & SQLite products.db)`  
**Verified Catalog Size:** `110 products (Frozen)`  

---

## 1. Executive Summary & Key Metrics

| Metric | Result | Evaluated | Status |
| :--- | :---: | :---: | :---: |
| **Overall Test Pass Rate** | **100.0%** | 56/56 tests | 🟢 PASS |
| **Retrieval Success Rate** | **100.0%** | 38/38 queries | 🟢 PASS |
| **Exact Constraint Accuracy** | **100.0%** | 33/33 queries | 🟢 PASS |
| **FAQ Retrieval Success Rate** | **100.0%** | 10/10 queries | 🟢 PASS |
| **Unknown Refusal Accuracy** | **100.0%** | 8/8 queries | 🟢 PASS |
| **Grounding / Zero-Hallucination** | **100.0%** | 56/56 tests | 🟢 PASS |

---

## 2. Test Case Distribution by Category

| Category | Total Queries | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| `product_category` | 15 | 15 | 0 | 100.0% |
| `price` | 10 | 10 | 0 | 100.0% |
| `size` | 8 | 8 | 0 | 100.0% |
| `faq` | 10 | 10 | 0 | 100.0% |
| `unknown` | 8 | 8 | 0 | 100.0% |
| `no_match` | 5 | 5 | 0 | 100.0% |

---

## 3. Individual Test Results Log

| ID | Category | Query | Status | Products | Intent | Details |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| `RAG001` | `product_category` | Show me necklaces | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG002` | `product_category` | Show me earrings | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG003` | `product_category` | Show me jhumkas | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG004` | `product_category` | Show me bridal jewellery | ✅ PASS | 2 | `catalog_search` | Satisfied constraints & behavior |
| `RAG005` | `product_category` | Show me bridal full sets | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG006` | `product_category` | Show me bridal combo sets | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG007` | `product_category` | Show me bridal bangles | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG008` | `product_category` | Show me glass bangles | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG009` | `product_category` | Show me combo boxes | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG010` | `product_category` | Show me broad kada bangles | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG011` | `product_category` | Show me budget kundan sets | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG012` | `product_category` | Show me ghungroo and metal bangles | ✅ PASS | 2 | `catalog_search` | Satisfied constraints & behavior |
| `RAG013` | `product_category` | Show me kids bangles | ✅ PASS | 1 | `catalog_search` | Satisfied constraints & behavior |
| `RAG014` | `product_category` | Show me scrunchies | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG015` | `product_category` | Show me hair clips | ✅ PASS | 1 | `catalog_search` | Satisfied constraints & behavior |
| `RAG016` | `price` | Show me products under ₹2000 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG017` | `price` | Show me products under ₹3000 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG018` | `price` | Show bridal jewellery under ₹3000 | ✅ PASS | 1 | `catalog_search` | Satisfied constraints & behavior |
| `RAG019` | `price` | Show products between ₹2000 and ₹5000 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG020` | `price` | Show earrings under ₹500 | ✅ PASS | 3 | `catalog_search` | Satisfied constraints & behavior |
| `RAG021` | `price` | Show necklaces under ₹1000 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG022` | `price` | Show bangles under ₹500 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG023` | `price` | Show bridal full sets under ₹2000 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG024` | `price` | Show jhumkas under ₹500 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG025` | `price` | Show products above ₹5000 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG026` | `size` | Do you have size 2.6? | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG027` | `size` | Show bangles in size 2.8 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG028` | `size` | Which bangles are available in size 2.6? | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG029` | `size` | Do you have size 2.4? | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG030` | `size` | Show bangles in size 2.2 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG031` | `size` | Show bangles in size 2.10 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG032` | `size` | Show bangles in size 2.12 | ✅ PASS | 4 | `catalog_search` | Satisfied constraints & behavior |
| `RAG033` | `size` | What sizes are available for this product? | ✅ PASS | 1 | `catalog_search` | Satisfied constraints & behavior |
| `RAG034` | `faq` | What is the return policy? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG035` | `faq` | What are the shipping options? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG036` | `faq` | Do you ship internationally? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG037` | `faq` | Do you offer rental jewellery? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG038` | `faq` | How can I contact RoSin? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG039` | `faq` | Who is the founder of RoSin? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG040` | `faq` | What are your store opening hours? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG041` | `faq` | What payment methods are accepted? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG042` | `faq` | How do I order a customized set to match my saree? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG043` | `faq` | What happens if my bangles are broken or damaged in transit? | ✅ PASS | 0 | `policy_faq` | Satisfied constraints & behavior |
| `RAG044` | `unknown` | What is the capital of France? | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG045` | `unknown` | What is today's weather? | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG046` | `unknown` | Write a Python program | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG047` | `unknown` | Who won yesterday's cricket match? | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG048` | `unknown` | Tell me a joke | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG049` | `unknown` | Who is the president of the United States? | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG050` | `unknown` | How do I bake a chocolate cake? | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG051` | `unknown` | What is the current price of Bitcoin? | ✅ PASS | 0 | `unknown` | Satisfied constraints & behavior |
| `RAG052` | `no_match` | Show bridal bangles under ₹2000 | ✅ PASS | 0 | `catalog_search` | Satisfied constraints & behavior |
| `RAG053` | `no_match` | Do you have size 3.5? | ✅ PASS | 0 | `catalog_search` | Satisfied constraints & behavior |
| `RAG054` | `no_match` | Do you have bangles in size 1.8? | ✅ PASS | 0 | `catalog_search` | Satisfied constraints & behavior |
| `RAG055` | `no_match` | Show bridal jewellery under ₹1000 | ✅ PASS | 0 | `catalog_search` | Satisfied constraints & behavior |
| `RAG056` | `no_match` | Show products under ₹50 | ✅ PASS | 0 | `catalog_search` | Satisfied constraints & behavior |
