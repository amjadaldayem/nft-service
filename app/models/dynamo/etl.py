# Respository for DynamoDB data access

class ETLTable:
    """
    Data repository for all ETL operations.

    """

    def __init__(self):
        self._create_table()

    def _create_table(self):
        """
        Single Table for storing ETL related information.

        Returns:

        """
