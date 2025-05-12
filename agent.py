import json
from prompts import system_prompt
from tools import query_sql
from tool_schema import TOOLS_SCHEMA


class Agent:
    def __init__(self, Model, VectorStore):
        self.client = Model.client
        self.vector_store = VectorStore
        self.model_name = Model.model_name
        self.tools = {
            "query_sql": query_sql
            }
        self.top_k = 50
        

    def call_model(self, context, merchants, descriptions, today):
        query = context["messages"]
        messages = [{"role": "system", "content": system_prompt(merchants, descriptions, today)}] + query
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.6,
                tools=TOOLS_SCHEMA
            )
        except Exception as e:
            context["messages"].append({"role": "assistant", "content": f"Model error: {e}"})
            return context

        reply = response.choices[0].message
        if reply.content and ("<tool_call" in reply.content or "<function" in reply.content):
            context["messages"].append({
                "role": "assistant",
                "content": "Error: Detected invalid manual tool call formatting. Please try rephrasing."
            })
            return context
        context["messages"].append(reply)
        return context

    def should_continue(self, context):
        last_msg = context["messages"][-1]
        print("Last Message: ", last_msg)
        if isinstance(last_msg, dict) and last_msg["role"] == "function":
            return "call_model"
        if last_msg.tool_calls:
            return "tools"
        if last_msg.content:
            return "end"
        return "end"
    
    def tool_node(self, context, client_id):
        last_msg = context["messages"][-1]
        if not hasattr(last_msg, "tool_calls"):
            return context

        tool_calls = last_msg.tool_calls
        print(tool_calls)
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
                if tool_name == "query_sql":
                    tool_args["client_id"] = str(client_id)
            except Exception as e:
                context["messages"].append({"role": "function", "name": tool_name, "content": f"Tool error: {e}"})
                continue

            tool_func = self.tools.get(tool_name)
            if tool_func:
                try:
                    result = tool_func(**tool_args)
                    context["messages"].append({"role": "function", "name": tool_name, "content": str(result)})
                except Exception as e:
                    context["messages"].append({"role": "function", "name": tool_name, "content": f"Tool error: {e}"})
            else:
                context["messages"].append({"role": "function", "name": tool_name, "content": "Tool not found"})
        return context
    
    def chat(self, query, client_id, today):
        context = {
            "messages": [],
            "state": "call_model",
        }
        context["messages"].append({"role": "user", "content": query})

        merchants, descriptions = self.vector_store.get_unique_merchants_and_descriptions(query, client_id, self.top_k)

        while context["state"] != "end":
            if context["state"] == "call_model":
                context = self.call_model(context, merchants, descriptions, today)
            elif context["state"] == "tools":
                context = self.tool_node(context, client_id)
            else:
                break

            context["state"] = self.should_continue(context)
        
        content = context["messages"][-1].content

        return content