## make a plan for what files in the curriculum need to be edited, and then make those edits
import os 
import psycopg2
from openai import OpenAI
import json

client = OpenAI()
csv_path = "./agents/curriculum/plan.md"
## create plan.md if it doesn't exist
if not os.path.exists(csv_path):
    with open(csv_path, "w") as plan:
        plan.write("# Curriculum Maintenance Plan\n\n")

curriculum_maintainer = client.beta.assistants.retrieve("asst_08QiismbxWNlXNDfWD0JiW3i")


def add_todo_to_plan(todo):
    ## write the todo to the end of plan.md as a markdown-formatted todo item
    with open(csv_path, "a") as plan:
        plan.write(f"- [ ] {todo}\n")







thread = client.beta.threads.create()

maintenance_prompt = f"Please use the vector store that is attached to make a currciulum maintenance plan for the files in the curriculum, then use your curriculum maintenance todo tool to add todos to the plan."
    
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=maintenance_prompt
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=curriculum_maintainer.id,
)

# Define the list to store tool outputs
tool_outputs = []
 
# Loop through each tool in the required action section
for tool in run.required_action.submit_tool_outputs.tool_calls:
  if tool.function.name == "add_todo_to_maintenance_plan":
        tool_kwargs = json.loads(tool.function.arguments)
        todo = tool_kwargs.get("todo")
        add_todo_to_plan(todo)
      
        tool_outputs.append({
            "tool_call_id": tool.id,
            "output": "success"
        })
 
# Submit all tool outputs at once after collecting them in a list
if len(tool_outputs) > 0:
  try:
    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
      thread_id=thread.id,
      run_id=run.id,
      tool_outputs=tool_outputs
    )
    print("Tool outputs submitted successfully.")
  except Exception as e:
    print("Failed to submit tool outputs:", e)
else:
  print("No tool outputs to submit.")
 

if run.status == 'completed': 
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print(messages.data[0].content[0].text.value)
    message = messages.data[0].content[0].text.value
    
else:
    print(run.status)
        