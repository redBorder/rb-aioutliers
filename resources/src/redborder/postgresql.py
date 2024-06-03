import asyncpg, asyncio
from resources.src.server.rest import config


class RbOutliersPSQL:

    RB_AIOUTLIERS_FILTERS_QUERY = "SELECT filter FROM saved_filters"

    def __init__(self) -> None:
        self.filters = []
        asyncio.run(self.get_filtered_data())

    async def get_filtered_data(self):
        connection = await asyncpg.connect(
            host=config.get("rbpsql", "host"),
            database=config.get("rbpsql", "database"),
            user=config.get("rbpsql", "user"),
            password=config.get("rbpsql", "password")
        )
        
        try:
            filtered_data = await connection.fetch(self.RB_AIOUTLIERS_FILTERS_QUERY)
            self.filters = [record['filter'] for record in filtered_data]
            print(self.filters)
        finally:
            await connection.close()