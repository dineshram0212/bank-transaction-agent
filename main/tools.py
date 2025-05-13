def query_sql(
        client_id: int,
        start_date: str = None,
        end_date: str = None,
        aggregation: str = None,
        direction: str = None,
        category: str = None,
        merchants: list[str] = None,
        descriptions: list[str] = None,
        group_by: list[str] = None,
        limit: int = None
) -> dict:
    """
    Builds query from the given parameters and query the database to return the results.
    """
    allowed_columns = {
        "bank_id", "acc_id", "txn_id", "txn_date", "desc", "amt", "cat", "merchant"
    }

    aggregations = {
        "sum": "SUM(amt)",
        "count": "COUNT(*)",
        "avg": "AVG(amt)",
        "max": "MAX(amt)",
        "min": "MIN(amt)"
    }

    if aggregation not in aggregations:
        raise ValueError("Invalid aggregation type")

    where_clauses = [f"clnt_id = {client_id}"]

    if start_date:
        where_clauses.append(f"txn_date >= '{start_date}'")
    if end_date:
        where_clauses.append(f"txn_date <= '{end_date}'")
    if direction:
        if direction.lower() == "spend":
            where_clauses.append("amt < 0")
        elif direction.lower() == "income":
            where_clauses.append("amt > 0")
        elif direction.lower() == "both":
            pass
        else:
            raise ValueError("Invalid direction: must be 'spend', 'income', or 'both'")

    if category:
        where_clauses.append(f"cat = '{category}'")
    if merchants and isinstance(merchants, list) and len(merchants) > 0:
        formatted = ', '.join([f'"{m.lower()}"' for m in merchants])
        where_clauses.append(f'LOWER("merchant") IN ({formatted})')
    if descriptions and isinstance(descriptions, list) and len(descriptions) > 0:
        desc_clauses = [f'LOWER("desc") LIKE \'%{d.lower()}%\'' for d in descriptions]
        where_clauses.append("(" + " OR ".join(desc_clauses) + ")")

    where_clause = " AND ".join(where_clauses)

    group_clause = ""
    select_fields = aggregations[aggregation]
    if group_by and isinstance(group_by, list) and len(group_by) > 0:
        group_clean = [col for col in group_by if col in allowed_columns]
        if not group_clean:
            raise ValueError("Invalid group by column(s)")
        group_clause = f" GROUP BY {', '.join(group_clean)}"
        select_fields = ', '.join(group_clean + [aggregations[aggregation]])

    sql_query = f"SELECT {select_fields} FROM transactions WHERE {where_clause}{group_clause}"
    if limit and isinstance(limit, int) and limit > 0:
        sql_query += f" LIMIT {limit}"

    return run_sql_query(sql_query)


def run_sql_query(query: str, db_path: str = "../data/transactions.db") -> dict:
    """
    Runs the given SQL query on the database and returns the results.
    """
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query)
        rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows}
    except Exception as e:
        return {"error": str(e), "query": query}


def visualize_data(data: dict, chart_type: str, x: str, y: str, title: str = ""):
    """
    Visualizes the given data using the specified chart type.
    """
    import pandas as pd
    import plotly.express as px

    charts = ["bar", "line", "area", "pie"]
    if chart_type not in charts:
        return {"error": f"Unsupported chart type: {chart_type}"}

    if "error" in data:
        return {"error": "Cannot visualize data with error."}
    if "rows" not in data:
        return {"error": "No data to visualize."}
    
    df = pd.DataFrame(data["rows"])

    if df.empty:
        return {"error": "DataFrame is empty."}

    cols = df.columns.tolist()
    # If x and y values are not provided or invalid, use the first two columns
    if x not in cols:
        x = cols[0] if len(cols) > 0 else None
    if y not in cols:
        y = cols[1] if len(cols) > 1 else None

    if not x or not y:
        return {"error": "Insufficient columns to generate chart."}

    df[x] = df[x].astype(str)
    df[y] = pd.to_numeric(df[y], errors="coerce")

    df = df.dropna(subset=[y])

    if df.empty or df[y].sum() == 0:
        return {"error": "No usable data after cleaning. Nothing to display."}

    df = df.sort_values(by=x)
    df = df.sort_values(by=y, ascending=False)

    fig = None
    if chart_type == "bar":
        fig = px.bar(df, x=x, y=y, title=title or f"{y} by {x}")
    elif chart_type == "line":
        fig = px.line(df, x=x, y=y, markers=True, title=title or f"{y} over {x}")
    elif chart_type == "area":
        fig = px.area(df, x=x, y=y, title=title or f"{y} over {x}")
    elif chart_type == "pie":
        df[y] = df[y].abs()
        fig = px.pie(df, names=x, values=y, title=title or f"{y} by {x}")
    else:
        return {"error": f"Unsupported chart type: {chart_type}"}

    return fig
