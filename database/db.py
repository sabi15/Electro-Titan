async def create_tables():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema = f.read()
    async with _pool.acquire() as conn:
        # Temporarily drop old tables to fix schema mismatch
        await conn.execute("""
            DROP TABLE IF EXISTS acc_accounts CASCADE;
            DROP TABLE IF EXISTS acc_history CASCADE;
            DROP TABLE IF EXISTS acc_usage CASCADE;
        """)
        # Recreate all tables from schema
        await conn.execute(schema)
