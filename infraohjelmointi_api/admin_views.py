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
from django.core.management import call_command
from io import BytesIO


def read_class_location_uploaded_file(request, excel):
    wb = load_workbook(filename=BytesIO(excel.read()), data_only=True, read_only=True)
    messages.success(
        request, "Successfully read Class/location Excel {}".format(excel.name)
    )
    buildHierarchies(
        wb=wb,
        rows=list(wb.worksheets[2].rows),
    )
    messages.success(request, "Successfully populated Class/location Excel data")


def excel_upload_view(request):
    projectFileHandler = None
    url = request.path_info
    urlToTitle = {
        "planning-excel-uploader": "Planning Excel Uploader",
        "budget-excel-uploader": "Budget Excel Uploader",
        "class-location-excel-uploader": "Class/Location Excel Uploader",
    }

    if request.method == "POST":
        excel = request.FILES["file"]
        if not excel.name.endswith(".xlsx"):
            messages.warning(request, "The wrong file type was uploaded")
            return HttpResponseRedirect(url)

        if url.endswith("planning-excel-uploader"):
            projectFileHandler = PlanningFileHandler()
        if url.endswith("budget-excel-uploader"):
            projectFileHandler = BudgetFileHandler()
        if url.endswith("class-location-excel-uploader"):
            read_class_location_uploaded_file(request, excel)
            url = reverse("admin:index")
            return HttpResponseRedirect(url)
        projectFileHandler.proceed_with_uploaded_file(request, excel)
        url = reverse("admin:index")
        return HttpResponseRedirect(url)

    form = ExcelUploadForm()
    data = {"form": form, "url": url, "uploader_title": urlToTitle[url.split("/")[2]]}
    return render(request, "excel_upload_form.html", data)
