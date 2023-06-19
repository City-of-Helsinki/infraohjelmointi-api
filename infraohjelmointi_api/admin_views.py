from infraohjelmointi_api.forms import ExcelUploadForm
from infraohjelmointi_api.management.commands.util.PlanningFileHandler import (
    PlanningFileHandler,
)
from infraohjelmointi_api.management.commands.util.BudgetFileHandler import (
    BudgetFileHandler,
)
from infraohjelmointi_api.management.commands.util.hierarchy import buildHierarchies
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from openpyxl import load_workbook
from io import BytesIO
from django.views import View


class ExcelFormView(View):
    form_class = ExcelUploadForm()
    form_template_name = "excel_upload_form.html"
    urlToTitle = {
        "planning-excel-uploader": "Planning Excel Uploader",
        "budget-excel-uploader": "Budget Excel Uploader",
        "class-location-excel-uploader": "Class/Location Excel Uploader",
    }

    def read_class_location_uploaded_file(self, request, excel):
        wb = load_workbook(
            filename=BytesIO(excel.read()), data_only=True, read_only=True
        )
        messages.success(
            request, "Successfully read Class/location Excel {}".format(excel.name)
        )
        buildHierarchies(
            wb=wb,
            rows=list(wb.worksheets[2].rows),
        )
        messages.success(request, "Successfully populated Class/location Excel data")

    def get(self, request, *args, **kwargs):
        url = request.path_info
        data = {
            "form": self.form_class,
            "url": url,
            "uploader_title": self.urlToTitle[url.split("/")[2]],
        }
        return render(request, "excel_upload_form.html", data)

    def post(self, request, *args, **kwargs):
        projectFileHandler = None
        url = request.path_info

        excel = request.FILES["file"]
        if not excel.name.endswith(".xlsx"):
            messages.warning(request, "The wrong file type was uploaded")
            return HttpResponseRedirect(url)

        if url.endswith("planning-excel-uploader"):
            projectFileHandler = PlanningFileHandler()
        if url.endswith("budget-excel-uploader"):
            projectFileHandler = BudgetFileHandler()
        if url.endswith("class-location-excel-uploader"):
            self.read_class_location_uploaded_file(request, excel)
            url = reverse("admin:index")
            return HttpResponseRedirect(url)
        projectFileHandler.proceed_with_uploaded_file(request, excel)
        url = reverse("admin:index")
        return HttpResponseRedirect(url)
