import sqlparse
import re
from collections import defaultdict
import random
import time

# Function to extract a query template as described in the paper
def extract_template(sql_query):
    # Step 1: Replace values in WHERE clause, SET, and VALUES with '?'
    # Replace string literals (e.g., 'example@mail.com') with '?'
    query_no_strings = re.sub(r"'[^']*'", "?", sql_query)

    # Replace numeric literals (e.g., 123 or 100.50) with '?'
    query_no_constants = re.sub(r"\b\d+(\.\d+)?\b", "?", query_no_strings)

    # Step 2: Parse the query to get the AST
    parsed = sqlparse.parse(query_no_constants)[0]

    # Function to recursively process the AST and normalize tokens
    def process_tokens(tokens):
        result = []
        for token in tokens:
            if token.is_group:
                result.append(process_tokens(token.tokens))
            else:
                # Normalize case for keywords and maintain original case for others
                result.append(token.value.upper() if token.ttype in sqlparse.tokens.Keyword else token.value)
        return ' '.join(result)

    # Process the tokens to normalize spacing, case, and bracket/parenthesis placement
    query_template = process_tokens(parsed.tokens)

    # Further cleanup of spaces and standardize parentheses
    query_template = re.sub(r'\s+', ' ', query_template).strip()
    query_template = re.sub(r'\s*\(\s*', ' (', query_template)  # Normalize opening parenthesis
    query_template = re.sub(r'\s*\)\s*', ' )', query_template)  # Normalize closing parenthesis

    return query_template

# Function to perform reservoir sampling
def reservoir_sampling(sample_size, items):
    sample = []
    for i, item in enumerate(items):
        if i < sample_size:
            sample.append(item)
        else:
            j = random.randint(0, i)
            if j < sample_size:
                sample[j] = item
    return sample

# Function to determine if two templates are semantically equivalent
def are_templates_equivalent(template1, template2):
    # Parse the templates
    parsed1 = sqlparse.parse(template1)[0]
    parsed2 = sqlparse.parse(template2)[0]

    # Extract operation type
    operation1 = parsed1.tokens[0].value.upper()
    operation2 = parsed2.tokens[0].value.upper()

    # If the operations are different, they are not equivalent
    if operation1 != operation2:
        return False

    # Extract table names, predicates, and projections
    def extract_features(parsed):
        tables = set()
        predicates = set()
        projections = set()
        for token in parsed.tokens:
            if token.ttype in {sqlparse.tokens.Name, sqlparse.tokens.Name.Builtin}:
                tables.add(token.value)
            elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() in {"WHERE", "SET", "VALUES"}:
                predicates.add(token.value.upper())
            elif token.ttype in {sqlparse.tokens.Wildcard, sqlparse.tokens.Name, sqlparse.tokens.Name.Builtin}:
                projections.add(token.value.upper())
        return tables, predicates, projections

    tables1, predicates1, projections1 = extract_features(parsed1)
    tables2, predicates2, projections2 = extract_features(parsed2)

    # Check if the templates are equivalent
    return tables1 == tables2 and predicates1 == predicates2 and projections1 == projections2

# Function to track query counts
class QueryTracker:
    def __init__(self):
        self.template_counts = defaultdict(int)
        self.start_time = time.time()
        self.time_interval = 60  # Time interval in seconds for counting queries

    def add_query(self, template):
        current_time = time.time()
        # If the time interval has passed, reset counts
        if current_time - self.start_time > self.time_interval:
            self.template_counts.clear()
            self.start_time = current_time
        
        self.template_counts[template] += 1

    def get_counts(self):
        return dict(self.template_counts)

# Example SQL queries (including additional examples)
sql_queries = [
    "SELECT name FROM users WHERE id = 123",
    "SELECT name FROM users WHERE id = 456",
    "INSERT INTO orders (user_id, amount) VALUES (1, 100.50), (2, 200.75)",
    "UPDATE users SET email = 'example@mail.com' WHERE id = 456",
    "DELETE FROM users WHERE last_login < '2024-01-01'",
    "SELECT * FROM orders WHERE user_id = 1 AND amount > 50",
    "INSERT INTO products (name, price) VALUES ('Widget', 19.99)",
    "SELECT COUNT(*) FROM users WHERE status = 'active'",
    "UPDATE products SET stock = stock - 1 WHERE id = 3",
    "SELECT DISTINCT category FROM products WHERE price < 100"
]

# Initialize QueryTracker
query_tracker = QueryTracker()

# Process the queries and extract templates
original_parameters = defaultdict(list)
sample_size = 5  # Example sample size for reservoir sampling

for sql in sql_queries:
    template = extract_template(sql)
    print(f"Extracted Template: {template}")  # Print the extracted template
    query_tracker.add_query(template)  # Track query counts
    original_parameters[template].append(sql)

# Perform reservoir sampling for original parameters
sampled_parameters = {template: reservoir_sampling(sample_size, params) for template, params in original_parameters.items()}

# Aggregate templates with equivalent semantic features
aggregated_templates = defaultdict(int)
for template1 in original_parameters:
    found_equivalent = False
    for template2 in list(aggregated_templates.keys()):  # Iterate over a list to avoid RuntimeError
        if are_templates_equivalent(template1, template2):
            aggregated_templates[template2] += len(original_parameters[template1])
            found_equivalent = True
            break
    if not found_equivalent:
        aggregated_templates[template1] = len(original_parameters[template1])

# Print the classification results
print("\nQuery Classification:")
for template, count in aggregated_templates.items():
    print(f"Template: {template}, Count: {count}")

# Print the sampled original parameters
print("\nSampled Original Parameters:")
for template, samples in sampled_parameters.items():
    print(f"Template: {template}, Samples: {samples}")

# Print the tracked counts of queries
print("\nTracked Query Counts:")
print(query_tracker.get_counts())
