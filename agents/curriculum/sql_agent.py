import os
import psycopg2
from openai import OpenAI

class SQLAgent:
    def __init__(self, database_url, api_key):
        self.database_url = database_url
        self.client = OpenAI(api_key=api_key)
        # self.assistant_id = self.client.beta.assistants.create(
        #     name="SQL Agent",
        #     instructions="You are an assistant that helps interact with a SQL database. Based on the user's input, determine the appropriate action to take.",
        #     model="gpt-4o"
        # )
        self.functions = [
            {
                "name": "get_all_tables",
                "description": "Retrieve a list of all tables in the public schema of the database.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_table_schema",
                "description": "Retrieve the schema details for specified tables within the database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_names": {
                            "type": "string",
                            "description": "A string of table names separated by spaces."
                        }
                    },
                    "required": ["table_names"]
                }
            },
            {
                "name": "execute_sql_query",
                "description": "Execute an arbitrary SQL query on the database.",
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
        ]
        self.assistant_id = "asst_8AebSxn6GNgmmp9kegkcuntH"
        self.assistant = self.client.beta.assistants.retrieve(self.assistant_id)
        self.assistant.functions = self.functions
        print(f"Assistant ID: {self.assistant_id}")

    def get_all_tables(self):
        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cur.fetchall()
        cur.close()
        conn.close()
        return [table[0] for table in tables]

    def get_table_schema(self, table_names):
        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()
        schema = {}
        for table in table_names.split():
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';")
            schema[table] = cur.fetchall()
        cur.close()
        conn.close()
        return schema

    def execute_sql_query(self, query):
        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()
        cur.execute(query)
        if query.strip().lower().startswith(("select", "show")):
            result = cur.fetchall()
        else:
            result = "Query executed successfully!"
            conn.commit()
        cur.close()
        conn.close()
        return result

    def sql_agent_interface(self, message_content):
        thread = self.client.beta.threads.create()
        
        message = self.client.beta.threads.messages.create(
            role="user",
            content=message_content,
            thread_id=thread.id
        )

        run = self.client.beta.threads.runs.create_and_poll(
            assistant_id=self.assistant_id,
            thread_id=thread.id
        )
        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )

            return messages.data[0].content[0].text.value
        else:

            required_action_section = run.required_action.submit_tool_outputs
            tool_calls = []

            for tool_call in required_action_section.tool_calls:
                tool_function_name = tool_call.selected_function_name
                tool_arguments = tool_call.function_arguments

                if tool_function_name == "get_all_tables":
                    output = self.get_all_tables()
                elif tool_function_name == "get_table_schema":
                    output = self.get_table_schema(tool_arguments["table_names"])
                elif tool_function_name == "execute_sql_query":
                    output = self.execute_sql_query(tool_arguments["query"])
                else:
                    output = "Unknown action. Please try again."

                tool_calls.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            if tool_calls:
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    tool_outputs=tool_calls
                )

        if run.status == 'completed':
            messages = thread.messages.list()
            return messages.data[0].content[0].text.value
        else:
            return run.status

if __name__ == "__main__":
    api_key = os.getenv('OPENAI_API_KEY')
    database_url = os.getenv('DATABASE_URL')

    sql_agent = SQLAgent(database_url, api_key)
    
    # Example usage
    print(sql_agent.sql_agent_interface("List all tables"))
    print(sql_agent.sql_agent_interface("Get schema for students students_classes"))
    print(sql_agent.sql_agent_interface("get all students emails"))