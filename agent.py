import json
import datetime
from tools_sample import TOOLS, get_transactions, aggregate_transactions
from prompts import SYSTEM_PROMPT

class ReactAgent:
    def __init__(self, Model):
        self.client = Model.client
        self.model_name = Model.model_name
        self.messages = []
        self.tools = {
            "get_transactions": get_transactions,
            "aggregate_transactions": aggregate_transactions
        }


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
    

    def call_model(self, context):
        messages = context["messages"]

        system_prompt = f"""
                        Today is {datetime.datetime.now().strftime('%d %B %Y,  %I:%M %p')}.
                        {SYSTEM_PROMPT}
                        """

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=full_messages,
            temperature=0.6,
            tools=TOOLS
        )

        reply = response.choices[0].message
        context["messages"].append(reply)
        
        if reply.content and ("<tool_call" in reply.content or "<function" in reply.content):
            context["messages"].append({
                "role": "assistant",
                "content": "Error: Detected invalid manual tool call formatting. Please try rephrasing."
                })
            return context

        return context

    def tool_node(self, context):
        last_msg = context["messages"][-1]
        if not hasattr(last_msg, "tool_calls"):
            return context

        print("ToolCall: ", last_msg.tool_calls)
        for tool_call in last_msg.tool_calls:
            tool_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except Exception as e:
                print(f"[TOOL ERROR] {tool_name} failed: {e}")
                context["messages"].append({
                    "role": "function",
                    "name": tool_name,
                    "content": f"Tool argument parsing error: {e}"
                })
                continue

            tool_func = self.tools.get(tool_name)
            if tool_func:
                try:
                    result = tool_func(**args)
                    context["messages"].append({"role": "function", "name": tool_name, "content": str(result)})
                except Exception as e:
                    context["messages"].append({"role": "function", "name": tool_name, "content": f"Tool error: {e}"})
        return context
    
    def run(self, user_input):

        context = {
            "messages": [],
            "state": "call_model",
        }

        context["messages"].append({"role": "user", "content": user_input})

        while context["state"] != "end":
            if context["state"] == "call_model":
                context = self.call_model(context)
            elif context["state"] == "tools":
                context = self.tool_node(context)
            else:
                break

            context["state"] = self.should_continue(context)

        last_msg = context["messages"][-1]

        clean_messages = [
            {"role": "user", "content": user_input},
            {"role": last_msg.role,"content": last_msg.content.replace(SYSTEM_PROMPT, "")}
            ]

        return context["messages"][-1].content
