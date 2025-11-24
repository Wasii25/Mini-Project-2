import asyncio
import json
import re
from datetime import datetime
from contextlib import AsyncExitStack
from typing import Optional, Dict

# MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LLM
from langchain_ollama.llms import OllamaLLM

import warnings

warnings.filterwarnings("ignore")

# Database connection string
DB_CONNECTION = "postgresql://student_user:student123@localhost:5432/student_db"


class PostgresSQLAgent:
    """SQL Agent using official PostgreSQL MCP server"""

    def __init__(self, model_name: str = "llama3.2:3b", verbose: bool = False):
        self.model_name = model_name
        self.llm = None
        self.session = None
        self.exit_stack = None
        self.schema_cache = None

        if verbose:
            print(f"Initializing {model_name}...")

        self.llm = OllamaLLM(
            model=model_name,
            temperature=0.1,
            num_ctx=2048,  # Reduced for speed
            num_thread=4,
        )

        if verbose:
            print("Model loaded")

    async def connect_mcp(self):
        """Connect to official PostgreSQL MCP server"""
        print(" Starting official PostgreSQL MCP server...")

        # Use the official MCP server
        server_params = StdioServerParameters(
            command="mcp-server-postgres", args=[DB_CONNECTION], env=None
        )

        self.exit_stack = AsyncExitStack()

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            read, write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            await self.session.initialize()

            # Get available tools
            tools = await self.session.list_tools()
            print(f" Connected to official MCP server")
            print(f" Available tools: {[t.name for t in tools.tools]}")

            # Get schema
            await self._load_schema()

        except Exception as e:
            print(f" Failed to connect to MCP server: {e}")
            print("\nTroubleshooting:")
            print(
                "1. Check if mcp-server-postgres is installed: which mcp-server-postgres"
            )
            print("2. Check if PostgreSQL is running: sudo systemctl status postgresql")
            print(
                "3. Test connection: psql postgresql://student_user:student123@localhost:5432/student_db"
            )
            raise

    async def _load_schema(self, verbose: bool = True):
        """Load database schema - with explicit fallback"""
        try:
            # Try to use MCP tools
            result = await self.session.call_tool("list_tables", {})
            tables_data = json.loads(result.content[0].text)

            # Build schema description
            self.schema_cache = {}
            schema_lines = ["Database Schema:\n"]

            for table_info in tables_data:
                table_name = table_info.get("table_name") or table_info.get("name")
                if table_name:
                    try:
                        schema_result = await self.session.call_tool(
                            "describe_table", {"table_name": table_name}
                        )
                        schema_data = json.loads(schema_result.content[0].text)
                        self.schema_cache[table_name] = schema_data

                        schema_lines.append(f"\nTable: {table_name}")
                        columns = []
                        for col in schema_data:
                            col_name = col.get("column_name") or col.get("name")
                            col_type = col.get("data_type") or col.get("type")
                            nullable = (
                                "NULL"
                                if col.get("is_nullable") == "YES"
                                else "NOT NULL"
                            )
                            columns.append(f"{col_name} {col_type} {nullable}")

                        schema_lines.append("  Columns: " + ", ".join(columns))
                    except:
                        pass

            # If MCP tools didn't work well, use explicit schema
            if not self.schema_cache or len(self.schema_cache) < 3:
                if verbose:
                    print("Using fallback explicit schema")
                schema_lines = self._get_explicit_schema()

            self.schema_description = "\n".join(schema_lines)
            if verbose:
                print("Schema loaded")

        except Exception as e:
            if verbose:
                print(f"Schema loading error: {e}, using explicit schema")
            self.schema_description = "\n".join(self._get_explicit_schema())

    def _get_explicit_schema(self) -> list:
        """Explicit schema definition as fallback"""
        return [
            "Database Schema:",
            "",
            "Table: students",
            "  Columns:",
            "    - id: INTEGER (PRIMARY KEY)",
            "    - first_name: TEXT",
            "    - last_name: TEXT",
            "    - dob: DATE",
            "    - email: TEXT",
            "",
            "Table: courses",
            "  Columns:",
            "    - id: INTEGER (PRIMARY KEY)",
            "    - code: TEXT (e.g., CS201, MATH101)",
            "    - title: TEXT (e.g., Algorithms, Calculus I)",
            "    - credits: INTEGER",
            "",
            "Table: enrollments",
            "  Columns:",
            "    - id: INTEGER (PRIMARY KEY)",
            "    - student_id: INTEGER (FOREIGN KEY → students.id)",
            "    - course_id: INTEGER (FOREIGN KEY → courses.id)",
            "    - enrolled_on: DATE",
            "    - grade: TEXT (e.g., A, A-, B+, B)",
            "",
            "⚠️ CRITICAL JOIN RULES:",
            "- To join students and enrollments: students.id = enrollments.student_id",
            "- To join enrollments and courses: enrollments.course_id = courses.id",
            "- NEVER use: enrollments.course_id = courses.code (wrong types!)",
            "",
            "⚠️ CRITICAL COLUMN RULES:",
            "- Students have 'first_name' and 'last_name' (NOT 'name')",
            "- Courses have 'code' (CS201) and 'title' (Algorithms)",
            "- Grades are in 'enrollments.grade' (NOT courses.grade)",
            "- Use WHERE courses.code = 'CS201' for course codes",
            "",
            "Example correct queries:",
            "- Students in CS201:",
            "  SELECT s.first_name, s.last_name",
            "  FROM students s",
            "  JOIN enrollments e ON s.id = e.student_id",
            "  JOIN courses c ON e.course_id = c.id",
            "  WHERE c.code = 'CS201'",
            "",
            "- Students with grade A:",
            "  SELECT s.first_name, s.last_name",
            "  FROM students s",
            "  JOIN enrollments e ON s.id = e.student_id",
            "  WHERE e.grade = 'A'",
        ]

    async def disconnect_mcp(self):
        """Cleanup MCP connection"""
        if self.exit_stack:
            await self.exit_stack.aclose()

    def generate_sql(self, question: str, verbose: bool = False) -> Optional[str]:
        """Generate SQL query from natural language"""
        prompt = f"""{self.schema_description}

User Question: {question}

Task: Generate a valid PostgreSQL SELECT query to answer this question.

Rules:
- Only SELECT statements (no INSERT, UPDATE, DELETE)
- Use proper PostgreSQL syntax
- Join tables when needed
- Limit to 20 rows max
- For course codes like CS201, use: WHERE code = 'CS201' (not title)
- Return ONLY the SQL query, no explanation

SQL Query:"""

        if verbose:
            print("  Generating SQL...")

        try:
            response = self.llm.invoke(prompt)
            sql = self._extract_sql(response)

            if sql and verbose:
                print(f"  Generated: {sql}")

            return sql

        except Exception as e:
            if verbose:
                print(f"  Generation error: {e}")
            return None

    def _extract_sql(self, text: str) -> Optional[str]:
        """Extract SQL from LLM response"""
        # Remove markdown
        text = re.sub(r"```sql\s*|\s*```", "", text)
        text = re.sub(r"```\s*|\s*```", "", text)

        # Remove prefixes
        text = re.sub(
            r"^(SQL Query:|Query:|Here.*?:|SELECT)", "SELECT", text, flags=re.IGNORECASE
        )

        # Take first statement
        text = text.split(";")[0].strip()

        if text.upper().startswith("SELECT"):
            return text

        # Try to find SELECT
        match = re.search(
            r"(SELECT\s+.*?FROM\s+\w+.*?)(?:;|\n|$)", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            return match.group(1).strip()

        return None

    async def execute_sql(self, sql: str, verbose: bool = False) -> Dict:
        """Execute SQL using official MCP server"""
        if verbose:
            print(f"  Executing: {sql}")

        try:
            result = await self.session.call_tool("query", {"sql": sql})

            result_text = result.content[0].text
            data = json.loads(result_text)

            if isinstance(data, list):
                if verbose:
                    print(f"  Success: {len(data)} rows")
                return {"success": True, "rows": data, "count": len(data)}
            elif isinstance(data, dict) and data.get("error"):
                if verbose:
                    print(f"  Error: {data['error']}")
                return {"success": False, "error": data["error"]}
            else:
                return {
                    "success": True,
                    "rows": [data] if data else [],
                    "count": 1 if data else 0,
                }

        except Exception as e:
            if verbose:
                print(f"  Execution error: {e}")
            return {"success": False, "error": str(e)}

    def format_answer(self, question: str, sql: str, result: Dict) -> str:
        """Format results into natural language"""
        if not result.get("success"):
            return f"I encountered an error: {result.get('error', 'Unknown error')}"

        rows = result.get("rows", [])
        count = result.get("count", 0)

        if count == 0:
            return "I couldn't find any results for your question."

        # Detect what type of data we have
        if not rows:
            return "No results found."

        first_row = rows[0]
        columns = list(first_row.keys())

        # CONSISTENT FORMATTING FOR ALL QUERIES

        # Case 1: Single value (like COUNT)
        if count == 1 and len(columns) == 1:
            value = first_row[columns[0]]
            return f"Result: {value}"

        # Case 2: Name columns (first_name + last_name)
        if "first_name" in columns and "last_name" in columns:
            names = [f"{row['first_name']} {row['last_name']}" for row in rows]
            if count == 1:
                return f"Found 1 student: {names[0]}"
            else:
                return f"Found {count} students: {', '.join(names)}"

        # Case 3: Single meaningful column (like table_name, code, title)
        if len(columns) == 1:
            col_name = columns[0]
            values = [str(row[col_name]) for row in rows]

            # Make the label natural based on column name
            if "name" in col_name:
                label = col_name.replace("_", " ").replace("name", "names")
            else:
                label = col_name.replace("_", " ") + "s"

            if count == 1:
                return f"Found 1 result: {values[0]}"
            else:
                return f"Found {count} results: {', '.join(values)}"

        # Case 4: Two columns (like code + title)
        if len(columns) == 2:
            formatted = [f"{row[columns[0]]} - {row[columns[1]]}" for row in rows]
            if count == 1:
                return f"Found 1 result: {formatted[0]}"
            elif count <= 10:
                return f"Found {count} results: {', '.join(formatted)}"
            else:
                preview = ", ".join(formatted[:5])
                return f"Found {count} results: {preview}, and {count - 5} more"

        # Case 5: Multiple columns (complex data)
        if count <= 3:
            # Show all data for small result sets
            lines = []
            for i, row in enumerate(rows, 1):
                parts = [f"{k}: {v}" for k, v in row.items() if v is not None]
                lines.append(f"Result {i}: {', '.join(parts)}")
            return "\n".join(lines)
        else:
            # Summarize for large result sets
            sample = rows[0]
            parts = [f"{k}: {v}" for k, v in sample.items() if v is not None]
            return f"Found {count} results. Example: {', '.join(parts)}"

        # OLD SLOW VERSION (commented out):
        # Prepare summary
        # if count <= 5:
        #     data_summary = json.dumps(rows, indent=2)
        # else:
        #     data_summary = json.dumps(rows[:5], indent=2) + f"\n... and {count - 5} more"
        #
        # prompt = f"""Question: {question}
        #
        # Results ({count} rows):
        # {data_summary}
        #
        # Task: Convert these results into a clear, conversational answer.
        # - Be natural and direct
        # - Mention specific names/numbers when relevant
        # - If many results, summarize
        # - Keep to 2-3 sentences
        #
        # Answer:"""
        #
        # print("  💬 Formatting answer...")
        #
        # try:
        #     answer = self.llm.invoke(prompt)
        #     return answer.strip()
        # except:
        #     # Fallback
        #     if count == 1:
        #         return f"Found 1 result: {rows[0]}"
        #     else:
        #         return f"Found {count} results."

    async def process_question(self, question: str, verbose: bool = False) -> str:
        """Main processing pipeline"""
        if verbose:
            print(f"\nQuestion: {question}")
            print("-" * 60)

        start_time = datetime.now()

        # Step 1: Generate SQL
        sql = self.generate_sql(question)

        if not sql:
            return (
                "I'm having trouble understanding your question. Could you rephrase it?"
            )

        # Step 2: Execute via official MCP
        result = await self.execute_sql(sql)

        # Step 3: Format answer
        answer = self.format_answer(question, sql, result)

        elapsed = (datetime.now() - start_time).total_seconds()

        if verbose:
            print(f"\nAnswer:")
            print(answer)
            print(f"\nProcessed in {elapsed:.2f} seconds")
            print("-" * 60)
        else:
            # Voice-friendly output: just the answer
            print(f"\n{answer}\n")

        return answer

    async def interactive_mode(self, verbose: bool = False):
        """Interactive Q&A"""
        print("\nSQL Agent Ready")
        print("Type 'exit' to quit")
        if verbose:
            print("Verbose mode: ON\n")
        else:
            print()

        while True:
            try:
                question = input("Question: ").strip()

                if not question:
                    continue

                if question.lower() in ["exit", "quit", "bye"]:
                    print("\nGoodbye\n")
                    break

                await self.process_question(question, verbose=verbose)

            except KeyboardInterrupt:
                print("\n\nGoodbye\n")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


async def main():
    """Entry point"""

    # Set verbose=True for debugging, False for voice mode
    verbose_mode = False  # Change to True to see debug info

    agent = PostgresSQLAgent(model_name="llama3.2:3b", verbose=verbose_mode)

    try:
        await agent.connect_mcp()
        await agent.interactive_mode(verbose=verbose_mode)
    except Exception as e:
        print(f"\nFatal error: {e}")
        if verbose_mode:
            import traceback

            traceback.print_exc()
    finally:
        await agent.disconnect_mcp()


if __name__ == "__main__":
    asyncio.run(main())
