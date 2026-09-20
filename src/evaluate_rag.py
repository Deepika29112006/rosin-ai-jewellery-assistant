import os
import sys
import json
import sqlite3
from datetime import datetime

# Configure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.rag_engine import get_rag, REFUSAL_MESSAGE
from src.db import get_db

EVAL_DATASET_PATH = os.path.join(PROJECT_ROOT, 'data', 'rag_evaluation.json')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
REPORT_JSON_PATH = os.path.join(REPORTS_DIR, 'rag_evaluation_report.json')
REPORT_MD_PATH = os.path.join(REPORTS_DIR, 'rag_evaluation_report.md')

def load_evaluation_dataset():
    if not os.path.exists(EVAL_DATASET_PATH):
        raise FileNotFoundError(f"Evaluation dataset not found at: {EVAL_DATASET_PATH}")
    with open(EVAL_DATASET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_ground_truth_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.title, p.handle, p.price, p.subcategory, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
    """)
    products = {r['id']: dict(r) for r in cursor.fetchall()}

    cursor.execute("SELECT DISTINCT product_id, size FROM product_variants WHERE size IS NOT NULL")
    variant_sizes = {}
    for r in cursor.fetchall():
        variant_sizes.setdefault(r['product_id'], set()).add(r['size'])

    conn.close()
    return products, variant_sizes

def evaluate_test_case(tc, rag, db_products, db_sizes):
    tc_id = tc['id']
    category = tc['category']
    query = tc['query']
    expected_behavior = tc.get('expected_behavior')
    expected_match = tc.get('expected_match', True)
    expected_constraints = tc.get('expected_constraints', {})
    expected_keywords = tc.get('expected_keywords', [])
    product_handle = tc.get('product_handle')

    # Execute query through the real RAG pipeline
    actual = rag.answer_query(query, product_handle=product_handle)

    reply = actual.get('reply', '')
    intent = actual.get('intent', '')
    rec_products = actual.get('recommended_products', [])
    citations = actual.get('citations', [])

    checks = {
        'retrieval_pass': False,
        'constraint_pass': False,
        'unknown_pass': False,
        'faq_pass': False,
        'grounding_pass': True,
        'overall_pass': False,
        'failure_reasons': []
    }

    # 1. RETRIEVAL SUCCESS
    if category in ['product_category', 'price', 'size']:
        if expected_match:
            if len(rec_products) > 0:
                checks['retrieval_pass'] = True
            else:
                checks['retrieval_pass'] = False
                checks['failure_reasons'].append(f"Expected >= 1 products but received 0")
        else:
            if len(rec_products) == 0 and ("no verified products" in reply.lower() or "no products were found" in reply.lower()):
                checks['retrieval_pass'] = True
            else:
                checks['retrieval_pass'] = False
                checks['failure_reasons'].append(f"Expected no-match response but got {len(rec_products)} products")

    elif category == 'no_match':
        # Correctly recognizing 0 matching items is a success
        if len(rec_products) == 0 and ("no verified products" in reply.lower() or "no products were found" in reply.lower()):
            checks['retrieval_pass'] = True
        else:
            checks['retrieval_pass'] = False
            checks['failure_reasons'].append(f"Expected 0 products with no-match notice, but received {len(rec_products)} products")

    elif category == 'faq':
        has_keywords = True
        if expected_keywords:
            has_keywords = any(kw.lower() in reply.lower() for kw in expected_keywords)
        if intent in ['policy_faq', 'hybrid'] and len(citations) > 0 and has_keywords:
            checks['retrieval_pass'] = True
            checks['faq_pass'] = True
        else:
            checks['retrieval_pass'] = False
            checks['faq_pass'] = False
            checks['failure_reasons'].append(f"FAQ intent/citations missing or keywords not in response")

    elif category == 'unknown':
        is_refusal = (
            intent == 'unknown'
            and len(rec_products) == 0
            and ("i don't know" in reply.lower() or "not available in the business data" in reply.lower())
        )
        if is_refusal:
            checks['retrieval_pass'] = True
            checks['unknown_pass'] = True
        else:
            checks['retrieval_pass'] = False
            checks['unknown_pass'] = False
            checks['failure_reasons'].append(f"Expected unknown refusal fallback but got intent='{intent}'")

    # 2. EXACT CONSTRAINT ACCURACY
    if expected_constraints and rec_products:
        constraint_violations = []
        for p in rec_products:
            pid = p['id']
            # Price constraints
            if 'max_price' in expected_constraints:
                max_p = float(expected_constraints['max_price'])
                if p['price'] > max_p:
                    constraint_violations.append(f"Product '{p['title']}' price ₹{p['price']} > max ₹{max_p}")
            if 'min_price' in expected_constraints:
                min_p = float(expected_constraints['min_price'])
                if p['price'] < min_p:
                    constraint_violations.append(f"Product '{p['title']}' price ₹{p['price']} < min ₹{min_p}")
            # Subcategory constraint
            if 'subcategory' in expected_constraints:
                sub = expected_constraints['subcategory']
                if p.get('subcategory') != sub:
                    constraint_violations.append(f"Product '{p['title']}' subcat '{p.get('subcategory')}' != '{sub}'")
            # Category constraint
            if 'category' in expected_constraints and not expected_constraints.get('subcategory'):
                cat = expected_constraints['category']
                if p.get('category') != cat:
                    constraint_violations.append(f"Product '{p['title']}' cat '{p.get('category')}' != '{cat}'")
            # Size constraint
            if 'size' in expected_constraints:
                sz = str(expected_constraints['size'])
                p_sizes = p.get('sizes') or []
                # Check if size is in product sizes
                if not any(sz == s or f"{sz}(" in s or f"{sz} " in s for s in p_sizes):
                    constraint_violations.append(f"Product '{p['title']}' sizes {p_sizes} does not include size {sz}")
            # Handle constraint
            if 'handle' in expected_constraints:
                h = expected_constraints['handle']
                if p.get('handle') != h:
                    constraint_violations.append(f"Product handle '{p.get('handle')}' != '{h}'")

        if constraint_violations:
            checks['constraint_pass'] = False
            checks['failure_reasons'].extend(constraint_violations)
        else:
            checks['constraint_pass'] = True
    else:
        # If no constraints or expected_match is false with 0 products
        checks['constraint_pass'] = True

    # 3. GROUNDING & HALLUCINATION CHECK
    for p in rec_products:
        pid = p['id']
        if pid not in db_products:
            checks['grounding_pass'] = False
            checks['failure_reasons'].append(f"Hallucinated product ID {pid} not found in database")
        else:
            db_p = db_products[pid]
            if float(p['price']) != float(db_p['price']):
                checks['grounding_pass'] = False
                checks['failure_reasons'].append(f"Price mismatch for {pid}: RAG gave ₹{p['price']} vs DB ₹{db_p['price']}")
            if p['handle'] != db_p['handle']:
                checks['grounding_pass'] = False
                checks['failure_reasons'].append(f"Handle mismatch for {pid}: RAG gave '{p['handle']}' vs DB '{db_p['handle']}'")

    # Overall pass: all applicable criteria passed
    checks['overall_pass'] = len(checks['failure_reasons']) == 0

    return {
        'id': tc_id,
        'category': category,
        'query': query,
        'intent': intent,
        'num_products_returned': len(rec_products),
        'returned_products': [{'id': p['id'], 'title': p['title'], 'price': p['price'], 'subcategory': p.get('subcategory')} for p in rec_products],
        'reply_snippet': reply[:160] + ('...' if len(reply) > 160 else ''),
        'citations': citations,
        'checks': checks,
        'passed': checks['overall_pass'],
        'failure_reasons': checks['failure_reasons']
    }

def run_evaluation():
    print("=" * 70)
    print("RoSin Bangles & Jewellery - Grounded RAG Evaluation Suite")
    print("=" * 70)

    dataset = load_evaluation_dataset()
    db_products, db_sizes = load_ground_truth_db()
    rag = get_rag()

    total_tests = len(dataset)
    results = []

    for idx, tc in enumerate(dataset, 1):
        res = evaluate_test_case(tc, rag, db_products, db_sizes)
        results.append(res)
        status = "PASS" if res['passed'] else "FAIL"
        print(f"[{idx:02d}/{total_tests:02d}] {res['id']} | {res['category'][:14]:<14} | {status} | {res['query']}")
        if not res['passed']:
            for reason in res['failure_reasons']:
                print(f"       -> ERROR: {reason}")

    # Calculate real, transparent metrics
    passed_tests = [r for r in results if r['passed']]
    failed_tests = [r for r in results if not r['passed']]

    product_queries = [r for r in results if r['category'] in ['product_category', 'price', 'size', 'no_match']]
    retrieval_successes = [r for r in product_queries if r['checks']['retrieval_pass']]
    retrieval_success_rate = (len(retrieval_successes) / len(product_queries) * 100.0) if product_queries else 100.0

    constraint_queries = [r for r in results if r['category'] in ['product_category', 'price', 'size']]
    constraint_successes = [r for r in constraint_queries if r['checks']['constraint_pass']]
    constraint_accuracy = (len(constraint_successes) / len(constraint_queries) * 100.0) if constraint_queries else 100.0

    faq_queries = [r for r in results if r['category'] == 'faq']
    faq_successes = [r for r in faq_queries if r['checks']['faq_pass']]
    faq_success_rate = (len(faq_successes) / len(faq_queries) * 100.0) if faq_queries else 100.0

    unknown_queries = [r for r in results if r['category'] == 'unknown']
    unknown_successes = [r for r in unknown_queries if r['checks']['unknown_pass']]
    unknown_refusal_rate = (len(unknown_successes) / len(unknown_queries) * 100.0) if unknown_queries else 100.0

    grounding_successes = [r for r in results if r['checks']['grounding_pass']]
    grounding_accuracy = (len(grounding_successes) / len(results) * 100.0) if results else 100.0

    overall_accuracy = (len(passed_tests) / total_tests * 100.0) if total_tests else 0.0

    # Summary dictionary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed': len(passed_tests),
        'failed': len(failed_tests),
        'overall_accuracy_pct': round(overall_accuracy, 2),
        'metrics': {
            'retrieval_success_rate_pct': round(retrieval_success_rate, 2),
            'retrieval_success_count': f"{len(retrieval_successes)}/{len(product_queries)}",
            'constraint_accuracy_pct': round(constraint_accuracy, 2),
            'constraint_accuracy_count': f"{len(constraint_successes)}/{len(constraint_queries)}",
            'faq_retrieval_rate_pct': round(faq_success_rate, 2),
            'faq_retrieval_count': f"{len(faq_successes)}/{len(faq_queries)}",
            'unknown_refusal_rate_pct': round(unknown_refusal_rate, 2),
            'unknown_refusal_count': f"{len(unknown_successes)}/{len(unknown_queries)}",
            'grounding_check_pct': round(grounding_accuracy, 2),
            'grounding_check_count': f"{len(grounding_successes)}/{total_tests}"
        },
        'category_counts': {
            'product_category': len([r for r in results if r['category'] == 'product_category']),
            'price': len([r for r in results if r['category'] == 'price']),
            'size': len([r for r in results if r['category'] == 'size']),
            'faq': len(faq_queries),
            'unknown': len(unknown_queries),
            'no_match': len([r for r in results if r['category'] == 'no_match'])
        }
    }

    # Generate Reports
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 1. JSON Report
    report_json_data = {
        'summary': summary,
        'test_results': results
    }
    with open(REPORT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(report_json_data, f, indent=2, ensure_ascii=False)

    # 2. Markdown Report
    generate_markdown_report(summary, results)

    # Print CLI Output
    print("\n" + "=" * 50)
    print("RoSin RAG Evaluation Summary")
    print("=" * 50)
    print(f"Total Tests Evaluated : {total_tests}")
    print(f"Passed                : {summary['passed']}")
    print(f"Failed                : {summary['failed']}")
    print(f"Overall Accuracy      : {summary['overall_accuracy_pct']}%")
    print("-" * 50)
    print(f"Retrieval Success Rate: {summary['metrics']['retrieval_success_rate_pct']}% ({summary['metrics']['retrieval_success_count']})")
    print(f"Constraint Accuracy   : {summary['metrics']['constraint_accuracy_pct']}% ({summary['metrics']['constraint_accuracy_count']})")
    print(f"FAQ Retrieval Rate    : {summary['metrics']['faq_retrieval_rate_pct']}% ({summary['metrics']['faq_retrieval_count']})")
    print(f"Unknown Refusal Rate  : {summary['metrics']['unknown_refusal_rate_pct']}% ({summary['metrics']['unknown_refusal_count']})")
    print(f"Grounding / Non-Halluc: {summary['metrics']['grounding_check_pct']}% ({summary['metrics']['grounding_check_count']})")
    print("=" * 50)
    print(f"JSON Report written to : {REPORT_JSON_PATH}")
    print(f"Markdown Report written: {REPORT_MD_PATH}")
    print("=" * 50)

    return summary['failed'] == 0

def generate_markdown_report(summary, results):
    lines = []
    lines.append("# RoSin AI Shopping Assistant - RAG Evaluation Report")
    lines.append("")
    lines.append(f"**Evaluation Timestamp:** `{summary['timestamp']}`  ")
    lines.append(f"**Target System:** `RoSin AI Shopping Assistant (RAGEngine & SQLite products.db)`  ")
    lines.append(f"**Verified Catalog Size:** `110 products (Frozen)`  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Executive Summary & Key Metrics")
    lines.append("")
    lines.append("| Metric | Result | Evaluated | Status |")
    lines.append("| :--- | :---: | :---: | :---: |")
    lines.append(f"| **Overall Test Pass Rate** | **{summary['overall_accuracy_pct']}%** | {summary['passed']}/{summary['total_tests']} tests | {'🟢 PASS' if summary['overall_accuracy_pct'] == 100 else '🟡 REVIEW'} |")
    lines.append(f"| **Retrieval Success Rate** | **{summary['metrics']['retrieval_success_rate_pct']}%** | {summary['metrics']['retrieval_success_count']} queries | {'🟢 PASS' if summary['metrics']['retrieval_success_rate_pct'] == 100 else '🟡 REVIEW'} |")
    lines.append(f"| **Exact Constraint Accuracy** | **{summary['metrics']['constraint_accuracy_pct']}%** | {summary['metrics']['constraint_accuracy_count']} queries | {'🟢 PASS' if summary['metrics']['constraint_accuracy_pct'] == 100 else '🟡 REVIEW'} |")
    lines.append(f"| **FAQ Retrieval Success Rate** | **{summary['metrics']['faq_retrieval_rate_pct']}%** | {summary['metrics']['faq_retrieval_count']} queries | {'🟢 PASS' if summary['metrics']['faq_retrieval_rate_pct'] == 100 else '🟡 REVIEW'} |")
    lines.append(f"| **Unknown Refusal Accuracy** | **{summary['metrics']['unknown_refusal_rate_pct']}%** | {summary['metrics']['unknown_refusal_count']} queries | {'🟢 PASS' if summary['metrics']['unknown_refusal_rate_pct'] == 100 else '🟡 REVIEW'} |")
    lines.append(f"| **Grounding / Zero-Hallucination** | **{summary['metrics']['grounding_check_pct']}%** | {summary['metrics']['grounding_check_count']} tests | {'🟢 PASS' if summary['metrics']['grounding_check_pct'] == 100 else '🔴 FAIL'} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Test Case Distribution by Category")
    lines.append("")
    lines.append("| Category | Total Queries | Passed | Failed | Pass Rate |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    for cat, total in summary['category_counts'].items():
        cat_res = [r for r in results if r['category'] == cat]
        p_count = len([r for r in cat_res if r['passed']])
        f_count = len([r for r in cat_res if not r['passed']])
        p_rate = (p_count / total * 100.0) if total else 0.0
        lines.append(f"| `{cat}` | {total} | {p_count} | {f_count} | {p_rate:.1f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Individual Test Results Log")
    lines.append("")
    lines.append("| ID | Category | Query | Status | Products | Intent | Details |")
    lines.append("| :--- | :--- | :--- | :---: | :---: | :--- | :--- |")
    for r in results:
        status_badge = "✅ PASS" if r['passed'] else "❌ FAIL"
        details = "Satisfied constraints & behavior" if r['passed'] else "; ".join(r['failure_reasons'])
        lines.append(f"| `{r['id']}` | `{r['category']}` | {r['query']} | {status_badge} | {r['num_products_returned']} | `{r['intent']}` | {details} |")
    lines.append("")

    with open(REPORT_MD_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

if __name__ == '__main__':
    success = run_evaluation()
    sys.exit(0 if success else 1)
