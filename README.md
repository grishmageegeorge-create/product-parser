# product-parser

A production-grade Python script that extracts structured product data from raw, unstructured text using the OpenAI API.

---

## What It Does

Given a messy product description like:

> "Nike Air Max 90 – great for running, just ₹4,500 only!"

It returns a clean, validated JSON object:

```json
{
  "name": "Nike Air Max 90",
  "price": 4500.0,
  "category": "Footwear"
}
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/grishmageegeorge-create/product-parser.git
cd product-parser
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

Create a `.env` file in the root folder:
OPENAI_API_KEY=your_actual_api_key_here

---

## How to Run

### Run a single test

```bash
python product_parser.py
```

### Run all 5 test cases

```bash
python test_inputs.py
```

Results are saved to `sample_outputs/results.json`.

---

## Project Structure
product-parser/
├── product_parser.py       # Main script
├── test_inputs.py          # 5 test cases
├── requirements.txt        # Dependencies
├── .env.example            # API key template
├── .gitignore              # Excludes .env and venv
├── sample_outputs/
│   └── results.json        # Output from test runs
└── README.md               # This file

---

## Design Decisions

### Model Choice
Used `gpt-4.1-mini` as it offers a strong balance between accuracy, speed, 
and cost — making it well suited for production extraction pipelines compared 
to older models.

### Approach 1: Function Calling (Primary)

The model is given a strict tool schema and forced to call it via `tool_choice`. This means field names and types are enforced at the API level. Price is typed as `number | null` so the model cannot return a string like "not listed".

### Approach 2: JSON Mode

The model is instructed via the system prompt to return a JSON object. This guarantees valid JSON but relies on prompt instructions for field names and types — less strict than function calling.

### Which is more reliable?

| Feature | Function Calling | JSON Mode |
|---|---|---|
| Schema enforcement | Strict | Prompt dependent |
| Type safety | High | Medium |
| Consistency | High | Medium |
| Recommended for production | Yes | Only for simple cases |

**Function calling is more reliable** because the schema is enforced at the API level, not left to prompt interpretation. You can also see this in the test results — function calling returns cleaner, more consistent categories like `"Footwear"` and `"Electronics"`, while JSON mode returns inconsistent ones like `"running shoes"` and `"electronics"`.

### Retry Mechanism

All API calls go through `call_with_retry()` which retries up to 3 times with exponential backoff (2s, 4s, 8s) on rate limit errors, connection errors, and API errors.