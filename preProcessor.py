import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML

# Function to extract a query template by tokenizing using sqlparse
def extract_template(sql_query):
    # Parse the query
    parsed = sqlparse.parse(sql_query)[0]

    # Initialize an empty list to hold tokens
    tokens_list = []

    # Walk through the parsed tokens
    for token in parsed.tokens:
        # Handle constants in WHERE, SET, and VALUES by replacing with '?'
        if token.ttype in [sqlparse.tokens.Literal.String.Single, sqlparse.tokens.Literal.Number.Integer]:
            tokens_list.append('?')
        # Include non-literal tokens as is
        else:
            tokens_list.append(str(token).strip())
    
    # Join tokens to form a query template
    template = ' '.join(tokens_list)
    
    return template

# Function to normalize and standardize the SQL query
def normalize_query(sql_query):
    # Parse the query
    parsed = sqlparse.parse(sql_query)[0]

    # Initialize an empty list to hold normalized tokens
    normalized_tokens = []

    # Walk through the tokens and normalize case, spaces, etc.
    for token in parsed.tokens:
        if isinstance(token, IdentifierList) or isinstance(token, Identifier):
            # Normalize identifiers (e.g., table and column names)
            normalized_tokens.append(token.get_real_name().lower())
        elif token.ttype == Keyword:
            # Normalize keywords to lowercase
            normalized_tokens.append(token.value.lower())
        else:
            # Keep other tokens (like operators) as is
            normalized_tokens.append(token.value)

    # Join tokens back to form a normalized SQL query
    normalized_query = ' '.join(normalized_tokens)
    
    return normalized_query

# Example usage
sql_queries = [
    "SELECT name FROM users WHERE id = 123",
    "INSERT INTO orders (user_id, amount) VALUES (1, 100.50)",
    "UPDATE users SET email = 'example@mail.com' WHERE id = 456"
]

# Process queries
for sql in sql_queries:
    normalized = normalize_query(sql)
    template = extract_template(sql)
    print(f"Normalized Query: {normalized}")
    print(f"Template: {template}")
