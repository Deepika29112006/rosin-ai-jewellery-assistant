# RoSin — AI-Powered Jewellery E-Commerce & RAG Shopping Assistant

A full-stack e-commerce platform built for a real jewellery business, featuring an AI-powered Retrieval-Augmented Generation (RAG) shopping assistant grounded in verified business and product data.

## 🚀 Overview

RoSin is an AI-powered jewellery shopping platform that combines a modern e-commerce website with a grounded RAG assistant.

The system allows customers to:

- Browse verified jewellery products
- Search products naturally
- Filter products by category and subcategory
- View product details
- Add products to cart
- Manage wishlist items
- Send enquiries through WhatsApp
- Ask the AI assistant about products, prices, sizes, shipping, returns and business information

The AI assistant is designed to answer only from verified RoSin business data and uses a strict fallback for unsupported questions.

## ✨ Key Features

### 🛍️ E-Commerce

- Product catalog with 110 verified products
- Category and subcategory filtering
- Product search
- Product detail pages
- Shopping cart
- Wishlist
- Responsive design
- WhatsApp enquiry/order flow

### 🤖 AI RAG Shopping Assistant

- Natural-language product queries
- Category-aware retrieval
- Subcategory-aware retrieval
- Price constraint handling
- Size-aware retrieval
- Business FAQ retrieval
- Shipping and return policy queries
- Strict unknown-question fallback
- Grounded responses using verified RoSin data
- Product results displayed directly in the chatbot

### 🔎 Grounded Retrieval

The system combines:

- Structured SQL retrieval for product catalog queries
- Semantic retrieval using FAISS
- Sentence Transformer embeddings
- Verified business knowledge documents
- Constraint-aware product filtering

The system avoids inventing products, prices, sizes or business policies that are not present in the verified dataset.

## 🧠 RAG Architecture

```text
User Query
    │
    ▼
Query Understanding
    │
    ├── Product / Catalog Query
    │       │
    │       ▼
    │   SQLite Retrieval
    │       │
    │       ▼
    │   Constraint Filtering
    │       │
    │       ▼
    │   Verified Products
    │
    └── Business / FAQ Query
            │
            ▼
       FAISS Semantic Retrieval
            │
            ▼
       Verified Knowledge
            │
            ▼
       Grounded Response