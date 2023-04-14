class IExcelFileHandler:
    """Interface class for handling excel file.\n
    Subclass must override and implement proceed_with_file method.
    """

    def proceed_with_file(self, excel_path, stdout, style):
        """Method to handle excel file."""
        pass
