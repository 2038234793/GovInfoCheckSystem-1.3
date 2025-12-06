import sqlite3
import json
from app import db
from sqlalchemy import text

def get_table_schema(table_name=None):
    """
    Returns the schema of the database tables.
    If table_name is provided, currently it ignores it and returns article_details schema,
    but the interface is kept for compatibility with AI tool calls.
    """
    # In a real scenario, we could filter by table_name if we had more tables.
    return """
CREATE TABLE article_details ( 
    id            INTEGER       NOT NULL, 
    crawl_item_id INTEGER       NOT NULL, 
    title         VARCHAR (256), 
    content       TEXT, 
    created_at    DATETIME      DEFAULT (CURRENT_TIMESTAMP), 
    PRIMARY KEY (id), 
    FOREIGN KEY (crawl_item_id) REFERENCES crawl_items (id), 
    UNIQUE (crawl_item_id) 
);
"""

def run_sql_query(query):
    """
    Executes a SQL query on the database and returns the results.
    """
    if not query or not isinstance(query, str):
        return "Error: Query must be a non-empty string."

    try:
        # Simple safety check - in production this needs to be much more robust
        # For this demo, we allow operations as requested.
        
        # Use SQLAlchemy connection to execute
        with db.engine.connect() as connection:
            result = connection.execute(text(query))
            
            # If it's a SELECT statement, return rows
            if query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = result.keys()
                return json.dumps([dict(zip(columns, row)) for row in rows], default=str, ensure_ascii=False)
            else:
                # For UPDATE/DELETE/INSERT, commit and return success
                connection.commit()
                return json.dumps({"status": "success", "rows_affected": result.rowcount})
                
    except Exception as e:
        return f"Error executing SQL: {str(e)}"

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_table_schema",
            "description": "Get the schema of the database tables (e.g. article_details) to understand structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Optional: The name of the table to get schema for (defaults to all important tables)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Execute a SQL query against the SQLite database. Use this to query, update, or delete data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def execute_tool_call(name, arguments):
    if name == "get_table_schema":
        # Accept table_name but ignore it for now as we only have one main table schema to show
        return get_table_schema(arguments.get('table_name'))
    elif name == "run_sql_query":
        query = arguments.get("query")
        return run_sql_query(query)
    else:
        return f"Unknown tool: {name}"
