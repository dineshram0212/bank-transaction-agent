import sqlite3

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
        if direction == "spend":
            where_clauses.append("amt < 0")
        elif direction == "income":
            where_clauses.append("amt > 0")
        elif direction == "both":
            pass
        else:
            raise ValueError("Invalid direction: must be 'spend', 'income', or 'both'")

    if category:
        where_clauses.append(f"cat = '{category}'")
    if merchants:
        formatted = ', '.join([f'"{m.lower()}"' for m in merchants])
        where_clauses.append(f'LOWER("merchant") IN ({formatted})')
    if descriptions:
        desc_clauses = [f'LOWER("desc") LIKE \'%{d.lower()}%\'' for d in descriptions]
        where_clauses.append("(" + " OR ".join(desc_clauses) + ")")

    where_clause = " AND ".join(where_clauses)

    group_clause = ""
    select_fields = aggregations[aggregation]
    if group_by:
        group_clean = [col for col in group_by if col in allowed_columns]
        if not group_clean:
            raise ValueError("Invalid group by column(s)")
        group_clause = f" GROUP BY {', '.join(group_clean)}"
        select_fields = ', '.join(group_clean + [aggregations[aggregation]])

    sql_query = f"SELECT {select_fields} FROM transactions WHERE {where_clause}{group_clause}"
    if limit:
        sql_query += f" LIMIT {limit}"

    return run_sql_query(sql_query)


def run_sql_query(query: str, db_path: str = "./data/transactions.db") -> dict:
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query)
        rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows}
    except Exception as e:
        return {"error": str(e)}
