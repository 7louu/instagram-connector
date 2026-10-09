class MongoRepositoryError(Exception):
    """Raised when a MongoDB or GridFS operation fails."""

class InstagramAPIError(Exception):
    """Raised when an Instagram API request fails or returns an invalid response."""