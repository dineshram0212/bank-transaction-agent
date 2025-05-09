import inspect
import re
from typing import Callable, Dict, Any

def extract_param_docs(docstring: str) -> Dict[str, Dict[str, str]]:
    """Parses the :param lines from a docstring."""
    param_docs = {}
    matches = re.findall(r":param (\w+): (.+)", docstring or "")
    for name, desc in matches:
        param_docs[name] = {"description": desc.strip()}
    return param_docs

def python_type_to_openai(python_type: Any) -> str:
    """Map Python types to OpenAI JSON schema types."""
    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }
    return mapping.get(python_type, "string")  # fallback to string

def tool(fn: Callable) -> Dict[str, Any]:
    """Generate OpenAI-style tool schema from a Python function with docstrings."""
    sig = inspect.signature(fn)
    param_docs = extract_param_docs(fn.__doc__)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "self":
            continue  
        param_type = python_type_to_openai(param.annotation)
        description = param_docs.get(name, {}).get("description", "No description provided.")
        properties[name] = {
            "type": param_type,
            "description": description
        }
        if param.default is inspect.Parameter.empty:
            required.append(name)

    tool_schema = {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": (fn.__doc__ or "").strip().split("\n")[0],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False
            },
            "strict": True
        }
    }

    fn.tool_schema = tool_schema
    return fn