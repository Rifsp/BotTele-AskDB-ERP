from app.database.connection import db


async def get_tables() -> list[dict]:
    query = """
        SELECT
            table_schema,
            table_name,
            pg_size_pretty(pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) as size,
            (SELECT COUNT(*) FROM information_schema.columns
             WHERE table_schema = t.table_schema AND table_name = t.table_name) as column_count,
            (SELECT COUNT(*) FROM information_schema.table_constraints
             WHERE table_schema = t.table_schema AND table_name = t.table_name) as constraint_count
        FROM information_schema.tables t
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
    """
    return await db.execute_query(query)


async def get_columns(table_schema: str, table_name: str) -> list[dict]:
    query = """
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
    """
    return await db.execute_query(query, [table_schema, table_name])


async def get_foreign_keys(table_schema: str, table_name: str) -> list[dict]:
    query = """
        SELECT
            kcu.column_name,
            ccu.table_schema AS foreign_schema,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = $1
            AND tc.table_name = $2
    """
    return await db.execute_query(query, [table_schema, table_name])


async def get_indexes(table_schema: str, table_name: str) -> list[dict]:
    query = """
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = $1 AND tablename = $2
        ORDER BY indexname
    """
    return await db.execute_query(query, [table_schema, table_name])


async def get_full_schema() -> dict:
    tables = await get_tables()
    result = []
    for table in tables:
        columns = await get_columns(table["table_schema"], table["table_name"])
        foreign_keys = await get_foreign_keys(table["table_schema"], table["table_name"])
        indexes = await get_indexes(table["table_schema"], table["table_name"])
        result.append({
            "schema": table["table_schema"],
            "table": table["table_name"],
            "size": table["size"],
            "column_count": table["column_count"],
            "constraint_count": table["constraint_count"],
            "columns": columns,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        })
    return {"tables": result}
