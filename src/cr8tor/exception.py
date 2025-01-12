class DirectoryNotFoundError(Exception):
    """Exception raised when a directory is not found."""

    def __init__(self, directory, message="Directory not found"):
        self.directory = directory
        self.message = f"{message}: {directory}"
        super().__init__(self.message)
