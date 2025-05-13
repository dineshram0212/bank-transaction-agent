TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "query_sql",
            "description": "Generates a SQL query to retrieve transaction summaries or aggregations based on the user's query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "The start date for the transaction filter in YYYY-MM-DD format."
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "The end date for the transaction filter in YYYY-MM-DD format."
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "count", "avg", "max", "min"],
                        "description": "The type of aggregation to perform on the transaction amounts."
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["spend", "income", "both"],
                        "description": "Filter transactions based on amount direction. 'spend' for negative, 'income' for positive, 'both' for all."
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter transactions by a specific category."
                    },
                    "merchants": {
                        "type": "array",
                        "items": {
                        "type": "string"
                        },
                        "description": "List of merchants to filter the transactions by (case-insensitive)."
                    },
                    "descriptions": {
                        "type": "array",
                        "items": {
                        "type": "string"
                        },
                        "description": "List of keywords to search for in the transaction descriptions."
                    },
                    "group_by": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "enum": ["bank_id", "acc_id", "txn_id", "txn_date", "desc", "amt", "cat", "merchant"]
                        },
                        "description": "Columns to group the results by."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Limit the number of rows returned."
                    }
                    },
                    "required": ["aggregation"]
                }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "visualize_data",
            "description": "Generate a visualization based on extracted structured transaction results.",
            "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                "type": "string",
                "enum": ["pie", "bar", "line", "area", "calendar"],
                "description": "The type of chart to generate."
                },
                "x": {
                "type": "string",
                "description": "Field to use on X-axis"
                },
                "y": {
                "type": "string",
                "description": "Field to use on Y-axis"
                },
                "title": {
                "type": "string",
                "description": "Title of the chart"
                }
            },
            "required": ["chart_type", "x", "y"]
            }
        }
    }
]