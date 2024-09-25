import sqlparse
import re

# Function to extract a query template as described in the paper
def extract_template(sql_query):
    # Step 1: Replace values in WHERE clause, SET, and VALUES with '?'
    # Replace string literals (e.g., 'example@mail.com') with '?'
    query_no_strings = re.sub(r"'[^']*'", "?", sql_query)

    # Replace numeric literals (e.g., 123 or 100.50) with '?'
    query_no_constants = re.sub(r"\b\d+(\.\d+)?\b", "?", query_no_strings)

    # Step 2: Normalize spacing and case (upper-case SQL keywords)
    parsed = sqlparse.format(query_no_constants, keyword_case='upper', strip_comments=True)

    # Step 3: Further cleanup of spaces, ensuring consistent single spacing
    query_template = re.sub(r'\s+', ' ', parsed).strip()
    
    return query_template

# Example SQL queries
sql_queries = [
    "SELECT name FROM users WHERE id = 123",
    "INSERT INTO orders (user_id, amount) VALUES (1, 100.50)",
    "UPDATE users SET email = 'example@mail.com' WHERE id = 456"
]

# Process the queries and extract templates
for sql in sql_queries:
    template = extract_template(sql)
    print(f"Template: {template}")
