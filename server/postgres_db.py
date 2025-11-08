import argparse
import logging
import traceback
import uvicorn
from typing import Optional, List, Dict, Any

from mcp.server import FastMCP
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("mcp-db")

# Parse command‑line arguments
parser = argparse.ArgumentParser(description="MCP Database Server")
parser.add_argument(
    "--db-url",
    dest="db_url",
    type=str,
    help="Database URL"
)

args = parser.parse_args()

# Get the DB URL from .env file
DB_URL = args.db_url
if not DB_URL:
    raise ValueError("DB_URL not Provided. Please provide `--db-url` to connect with database.")

# Build the SQLAlchemy engine
engine: Engine = create_engine(DB_URL, pool_pre_ping=True)
mcp = FastMCP(debug=True)
# app = mcp.streamable_http_app()


class SQLQueryResult(BaseModel):
    success: bool
    sql: str
    row_count: int
    rows: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@mcp.resource(
    uri="db://sample-data/{table_name}",
    name="Sample data for table",
    title="Sample data and schema for {table_name}",
    description="Provides a few sample rows and the column schema for the given table, to help an LLM understand the "
                "structure before running queries.",
    mime_type="application/json"
)
async def sample_data_resource(table_name: str) -> dict:
    """
    Returns sample schema info and up to N rows of data for the specified table.
    Useful for LLMs to inspect structure before building queries.
    """
    inspector = inspect(engine)
    try:
        # Get columns
        cols = [col["name"] for col in inspector.get_columns(table_name)]
        # Get sample rows (limit e.g. 5)
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
            rows = [dict(r._mapping) for r in result]
        return {
            "table": table_name,
            "columns": cols,
            "sample_rows": rows
        }
    except Exception as e:
        logger.error(f"Error fetching sample data for table {table_name}: {e}")
        return {
            "table": table_name,
            "columns": [],
            "sample_rows": [],
            "error": str(e)
        }


@mcp.tool(
    name="list_tables",
    title="List Database Tables",
    description="List all tables in the connected database. you can use this in case you don't know tables in "
                "database."
)
async def list_tables() -> dict:
    """Return a list of table names."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    response = {"tableList": tables}
    return response


@mcp.resource(
    uri="db://metadata/{table_name}",
    name="describe_table",
    mime_type="application/json",
    title="Describe Table Schema",
    description="Describe the columns and types of a given table. Returns the column names, types, "
                "nullability and defaults for a given table. You can call this tool in case needs to learn about "
                "table structure.")
async def describe_table(table_name: str) -> dict:
    """Describe a specific table's schema."""
    inspector = inspect(engine)
    columns = []
    for col in inspector.get_columns(table_name):
        columns.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col["nullable"],
            "default": col.get("default"),
        })

    response = {"table": table_name, "columns": columns}
    return response


@mcp.tool(name="run_sql", title="Run SQL Query", description="Execute a SQL query and return results.",
          structured_output=True)
async def run_sql(sql_query: str) -> SQLQueryResult:
    """Execute raw SQL queries safely."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            if result.returns_rows:
                rows = [dict(r._mapping) for r in result]
                return SQLQueryResult(success=True, sql=sql_query, row_count=len(rows), rows=rows)
            else:
                conn.commit()
                return SQLQueryResult(success=True, sql=sql_query, row_count=result.rowcount)
    except SQLAlchemyError as e:
        logger.error(f"SQL error: {e}")
        return SQLQueryResult(success=False, sql=sql_query, row_count=0, error=str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return SQLQueryResult(success=False, sql=sql_query, row_count=0, error=str(e))


@mcp.prompt(
    name="handle_query_error",
    title="Handle SQL query error",
    description="When a SQL query fails, guide the model to inspect tables or schema and retry safely."
)
async def handle_query_error(error_message: str, table_name: Optional[str] = None, sql_query: Optional[str] = None):
    messages = [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"You attempted to run this SQL query:\n{sql_query}\n\n"
                    f"It failed with the error:\n{error_message}\n\n"
                    "Here are your options:\n"
                    "1. Call list_tables() to check available tables.\n"
                    "2. Call describe_table(table_name) to inspect schema of the target table.\n"
                    "3. Once you have correct schema/columns, craft a corrected SQL and call run_sql().\n"
                    "Which step will you take?"
                )
            }
        }
    ]
    return {"description": "...", "messages": messages}


if __name__ == "__main__":
    mcp.run()
    # uvicorn.run(app)
