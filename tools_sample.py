import logging

logger = logging.getLogger(__name__)

def get_transactions(query, start_date=None, end_date=None, amount_op=None, amount_value=None, limit=500):
    logger.info(f"[Tool] get_transactions: query='{query}', start_date={start_date}, end_date={end_date}, amount_op={amount_op}, amount_value={amount_value}")
    return [{"txn_date": "2025-05-01", "merchant": "Uber", "amt": 242.50}]  # mocked for now

import ast  # for safe literal parsing

def aggregate_transactions(records, agg):
    # Convert stringified list to Python list if needed
    if isinstance(records, str):
        try:
            records = ast.literal_eval(records)
        except Exception as e:
            return {"error": f"Failed to parse records: {e}"}
    
    logger.info(f"[Tool:aggregate_transactions] {len(records)} records, agg={agg}")
    
    try:
        amounts = [r["amt"] for r in records]
        if not amounts:
            return {"result": 0}
        
        if agg == "sum":
            return {"result": round(sum(amounts), 2)}
        elif agg == "count":
            return {"result": len(amounts)}
        elif agg == "avg":
            return {"result": round(sum(amounts) / len(amounts), 2)}
        else:
            return {"error": f"Unknown aggregation: {agg}"}
    
    except Exception as e:
        return {"error": f"Tool failed: {e}"}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Retrieve bank transactions filtered by keywords, dates, or amounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":        {"type": "string"},
                    "start_date":   {"type": "string", "nullable": True},
                    "end_date":     {"type": "string", "nullable": True},
                    "amount_op":    {"type": "string", "enum": ["gt", "lt"], "nullable": True},
                    "amount_value": {"type": "number", "nullable": True},
                    "limit":        {"type": "integer", "default": 500}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aggregate_transactions",
            "description": "Aggregate a list of transactions (sum, count, avg, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "records": {"type": "array", "items": {"type": "object"}},
                    "agg": {"type": "string", "enum": ["sum", "count", "avg"]}
                },
                "required": ["records", "agg"]
            }
        }
    }
]