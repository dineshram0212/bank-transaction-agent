import json
from plotly.graph_objs import Figure

from prompts import system_prompt
from tools import query_sql, visualize_data
from tool_schema import TOOLS_SCHEMA


class Agent:
    def __init__(self, Model, VectorStore):
        self.client = Model.client
        self.vector_store = VectorStore
        self.tools = {
            "query_sql": query_sql,
            "visualize_data": visualize_data
            }
        self.top_k = 50
        self.history_limit = 8
        self.last_result = None
        self.chart = None

    def call_model(self, context, merchants, descriptions, today, model_name):
        """
        Calls the model with the given context, merchants, descriptions, today, and model name.
        """
        query = context["messages"]
        messages = [{"role": "system", "content": system_prompt(merchants, descriptions, today)}] + query
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.6,
                tools=TOOLS_SCHEMA
            )
        except Exception as e:
            context["messages"].append({"role": "assistant", "content": f"Model error: {e}"})
            return context

        reply = response.choices[0].message
        # Return error if the tool call is being manually added to the content
        if reply.content and ("<tool_call" in reply.content or "<function" in reply.content):
            context["messages"].append({
                "role": "assistant",
                "content": "Error: Detected invalid manual tool call formatting. Please try rephrasing."
            })
            return context
        print("Debug: ", reply)
        if reply.tool_calls:
            context["messages"].append({"role": reply.role, "tool_calls": [tc.model_dump() for tc in reply.tool_calls]})
        elif reply.content:
            context["messages"].append({"role": reply.role, "content": reply.content})

        return context

    def should_continue(self, context):
        """
        Determines if the conversation should continue.
        """
        if not context["messages"]:
            return "end"
        last_msg = context["messages"][-1]

        if not isinstance(last_msg, dict):
            try:
                last_msg = last_msg.model_dump()
            except:
                last_msg = {
                    "role": getattr(last_msg, "role", None),
                    "content": getattr(last_msg, "content", None),
                    "tool_calls": getattr(last_msg, "tool_calls", None)
                }
        # Return to end if the last message is an error
        if last_msg.get("content") and "error" in last_msg.get("content", "").lower():
            return "end"
        # Return to call_model if the last message is a function call
        if last_msg.get("role") == "function":
            return "call_model"
        # Return to tools if the last message is a tool call
        elif last_msg.get("tool_calls"):
            return "tools"
        else:
            return "end"
    
    def tool_node(self, context, client_id):
        """
        Executes the tool calls.
        """
        last_msg = context["messages"][-1]
        tool_calls = None
        if isinstance(last_msg, dict):
            tool_calls = last_msg.get("tool_calls")
        else:
            tool_calls = getattr(last_msg, "tool_calls", None)
        if not tool_calls:
            return context
        # Loop over available tool calls
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call.get("function", {}).get("name")
                tool_args = tool_call.get("function", {}).get("arguments")
            else:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
            # Return error if the tool is not registered
            if not tool_name:
                context["messages"].append({"role": "function", "name": tool_name, "content": "Invalid tool call"})
                continue
            try:
                tool_args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
                tool_func = self.tools.get(tool_name)
                if not tool_func:
                    context["messages"].append({"role": "function", "name": tool_name, "content": "Tool not found"})
                    continue
                
                if tool_name == "query_sql":
                    tool_args["client_id"] = str(client_id) # Add client_id to the tool arguments
                    result = tool_func(**tool_args)
                    self.last_result = result
                    context["messages"].append({"role": "function", "name": tool_name, "content": str(result)})

                elif tool_name == "visualize_data":
                    if self.last_result:
                        allowed_keys = ["chart_type", "x", "y", "title"]
                        tool_args = {k: v for k, v in tool_args.items() if k in allowed_keys} # Avoid extra arguments
                        tool_args["data"] = self.last_result
                        result = tool_func(**tool_args)
                        if isinstance(result, Figure):
                            context["messages"].append({"role": "function", "name": tool_name, "content": "Chart generated"})
                            self.chart = result
                        else:
                            context["messages"].append({"role": "function", "name": tool_name, "content": "Error: Chart not generated."})
                    else:
                        context["messages"].append({"role": "function", "name": tool_name, "content": "Error: No data to visualize."})

            except Exception as e:
                context["messages"].append({"role": "function", "name": tool_name, "content": f"Tool error: {e}"})
                continue
        return context
    
    def chat(self, query, client_id, today, message_history=None, model_name=None):
        """
        Main function to start the conversation.
        """
        if message_history:
            trimmed_history = [m for m in message_history if m["role"] in ["user", "assistant"]][-self.history_limit:]
        else:
            trimmed_history = []
        context = {
            "messages": trimmed_history + [{"role": "user", "content": query}],
            "state": "call_model",
        }
        # Get unique merchants and descriptions from the vector store
        merchants, descriptions = self.vector_store.get_unique_merchants_and_descriptions(query, client_id, self.top_k)

        while context["state"] != "end":
            if context["state"] == "call_model":
                context = self.call_model(context, merchants, descriptions, today, model_name)
            elif context["state"] == "tools":
                context = self.tool_node(context, client_id)
            else:
                break

            context["state"] = self.should_continue(context)

        last_msg = context["messages"][-1]

        if isinstance(last_msg, dict):
            content = last_msg.get("content", "")
        else:
            content = last_msg.content
        chart = self.chart
        self.chart = None # Delete the class variable so it doesn't get displayed again
        return {"content": content,"chart": chart}


