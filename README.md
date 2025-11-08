
# MCP Server with SQL Alchemy and Gemini LLM

This project implements a Model Context Protocol (MCP) server that provides a bridge between a PostgreSQL database and an AI agent powered by Google's Gemini LLM. The server allows natural language interactions with the database through MCP endpoints.

## Features

- SQL Alchemy integration for database operations
- MCP Server implementation with standardized endpoints
- Gemini LLM-powered agent for natural language database interactions
- PostgreSQL database support
- Structured query processing and response handling

## Project Structure

```
mcp-server-client/
├── main.py              # Main application entry point
├── pyproject.toml       # Project dependencies and configuration
├── client/             
│   ├── __init__.py     
│   └── db_client.py    # Database client implementation
├── server/             
│   ├── __init__.py    
│   ├── postgres_db.py  # PostgreSQL database connection and operations
│   └── weather.py      # Weather-related functionality
```


## Installation

1. install uv:
```bash
pip install uv
```
2. activate virtual environment'
```bash
# for linux
source .venv/bin/activate

# for windows
.venv\Scripts\activate

```

3. Install dependencies:
```bash
uv add mcp[cli] mcp-use psycopg2 psycopg2-binary sqlalchemy langchain-google-genai
```

4. Set up environment variables:
```bash
# create .env file
touch .env

# add this into .env file
# PostgreSQL connection
DB_URL= "postgresql://postgres:admin@localhost:5432/mydb"
GEMINI_API_KEY= "API_KEY"
```
5. start the agent
```bash
uv run client/db_client.py 
```

## Example Interactions

Below are some examples of interactions with the SQL agent:

![alt text](images/image.png)
![alt text](images/image-1.png)
![alt text](images/image-2.png)
![alt text](images/image-3.png)
![alt text](images/image-4.png)
![alt text](images/image-5.png)
![alt text](images/image-6.png)
![alt text](images/image-7.png)
![alt text](images/image-8.png)
![alt text](images/image-9.png)

