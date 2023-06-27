class IExcelFileHandler:
    """Interface class for handling excel file.\n
    Subclass must override and implement proceed_with_file method.
    """

    def proceed_with_file(self, excel_path):
        """Method to handle excel file."""
        pass

    def proceed_with_uploaded_file(self, request, uploadedFile):
        """Method to handle uploaded excel file."""
        pass

    def proceed_with_excel_data(self, wb):
        """Method to handle excel data."""
        pass
