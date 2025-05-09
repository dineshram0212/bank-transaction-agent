from tool_decorator import tool

@tool
def get_transactions(query):
    """
    Execute a SQL query on the transactions database and return results as a pandas DataFrame
    
    :param query: SQL query to execute
    """
    import pandas as pd
    import sqlite3

    # Connect to database
    conn = sqlite3.connect('transactions.db')

    try:
        # Execute query and load result into DataFrame
        df = pd.read_sql_query(query, conn)

        if df.shape == (1, 1):
            # Single value result (like SELECT COUNT(*))
            return {
                "type": "scalar",
                "value": df.iat[0, 0]
            }
        else:
            # Multi-row or multi-column result
            return {
                "type": "table",
                "data": df.to_dict(orient="records")
            }
    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }
    finally:
        conn.close()
