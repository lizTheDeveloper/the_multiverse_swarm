import json
from openai import OpenAI

class Model:
    def __init__(self, api_key="lm-studio", base_url="http://localhost:1234/v1", model_name="lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF", system_message="You are a helpful assistant.", tools=[]):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name
        self.system_message = system_message
        self.tools = tools

    def generate_response(self, messages, temperature=0.7, max_tokens=2048, max_retries=20):
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json"},
                    max_tokens=max_tokens
                )
                result = completion.choices[0].message.content
                try: 
                    json_result = json.loads(result)
                    
                    if json_result.get("type", None) == "function":
                        tool_call = self.get_tool_call(json_result)
                        messages.append(tool_call)
                        break
                except Exception as e:
                    messages.append({"role": "assistant", "content": result})
                    messages.append({"role": "user", "content": "Your previous response was invalid. Please retry. Please respond only with JSON with no other text so we can retry the result. The error we got was: " + str(e)})
                    continue
                ## validate that the response has a type of message or function
                if json_result.get("type", None) not in ["message", "function"]:
                    messages.append({"role": "assistant", "content": result})
                    messages.append({"role": "user", "content": "Your previous response was invalid. Please retry. Please respond only with JSON with no other text so we can retry the result."})
                    continue
                
                if result == "":
                    print("Empty response. Retrying...")
                    messages.append({"role": "user", "content": "Your previous response was empty. Please retry."})
                    continue
                return json.loads(result)
            except json.JSONDecodeError as e:
                print(completion.choices[0].message.content)
                print(messages)
                print(f"Attempt {attempt + 1}: Failed to parse JSON. Retrying...")
                messages.append({"role": "user", "content": "Your previous response was invalid. Please retry. Please respond only with JSON so we can retry the result. Here's the error we got: " + str(e)})
            except Exception as e:
                print(f"Attempt {attempt + 1}: An error occurred: {str(e)}. Retrying...")
            
            messages = [message for message in messages if message.get('content', None) is not None]
        
        raise RuntimeError(f"Failed to get valid response from model after {max_retries} attempts")

    def get_system_message(self):
        base_message = f"""
Your role is to respond with either a single message or a single tool call in JSON format only with no other text. Messages should be formatted as JSON, and any other explanatory text should be formatted as JSON. Do not respond outside of the JSON format, do not produce fenced code blocks, only JSON.
For messages, use the following structure:
{{
    "type": "message",
    "content": "Your message here",
    "finished": false
}}

For tool calls, use the OpenAI function-calling standard:
{{
    "type": "function",
    "function": {{
        "name": "function_name",
        "arguments": {{
            "arg1": "value1",
            "arg2": "value2"
        }}
    }}
}}

When you're finished with the task, send a final message with "finished": true.

{self.system_message}

Available tools:
"""
        return base_message + json.dumps(self.tools, indent=2)

    def run_agent_step(self, messages):
        return self.generate_response(messages)
    
    def get_tool_call(self, json_result):
        ## search your tools for the function
        for tool in self.tools:
            if tool["name"] == json_result["function"]["name"]:
                return {
                    "role": "system",
                    "content": json.dumps(json_result)
                }