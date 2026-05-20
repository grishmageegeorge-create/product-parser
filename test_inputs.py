"""
test_inputs.py
--------------
Runs all 5 test cases through both parsing approaches and saves
the results to sample_outputs/results.json.
"""

import json
import os
from product_parser import parse_product

TEST_INPUTS = [
    {
        "id": 1,
        "description": "Messy text with Indian currency symbol",
        "text": "Nike Air Max 90 – great for running, just ₹4,500 only!",
    },
    {
        "id": 2,
        "description": "Pipe-separated with USD price",
        "text": "Sony WH-1000XM5 | Wireless Headphones | Electronics | $349.99",
    },
    {
        "id": 3,
        "description": "Approximate price in rupees, informal language",
        "text": "Handmade brown leather wallet, costs approx 850 rupees, accessories",
    },
    {
        "id": 4,
        "description": "Missing price field",
        "text": "Organic green tea powder — no price listed, health & wellness",
    },
    {
        "id": 5,
        "description": "Indian number format with specs in text",
        "text": "ASUS ROG Strix laptop, gaming, 16GB RAM, priced at 1,20,000 INR",
    },
]


def run_tests(approach: str = "function_calling") -> list:
    """Run all test inputs through the parser and return results."""
    results = []
    for case in TEST_INPUTS:
        print(f"\n{'='*60}")
        print(f"Test {case['id']}: {case['description']}")
        print(f"Input: {case['text']}")
        output = parse_product(case["text"], approach=approach)
        print(f"Output: {output}")
        results.append(
            {
                "id": case["id"],
                "description": case["description"],
                "input": case["text"],
                "approach": approach,
                "output": output,
            }
        )
    return results


if __name__ == "__main__":
    os.makedirs("sample_outputs", exist_ok=True)

    print("\n APPROACH 1: Function Calling")
    fc_results = run_tests("function_calling")

    print("\n\n APPROACH 2: JSON Mode")
    jm_results = run_tests("json_mode")

    all_results = {"function_calling": fc_results, "json_mode": jm_results}

    output_path = os.path.join("sample_outputs", "results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n Results saved to {output_path}")