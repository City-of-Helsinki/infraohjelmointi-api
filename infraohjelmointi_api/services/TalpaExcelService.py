from io import BytesIO
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill


class TalpaExcelService:
    """Generates Projektin avauslomake Infra Excel for Talpa submission."""

    COLUMNS = [
        ("A", "Talousarviokohdan numero", "budgetAccount", 25),
        ("B", "Projektinumeroväli", "_numberRange", 25),
        ("C", "Malliprojekti", "templateProject", 15),
        ("D", "Laji", "_typeCode", 10),
        ("E", "Prioriteetti", "_typePriority", 12),
        ("F", "SAP nimi", "projectName", 25),
        ("G", "Projekti alkaa", "_startDate", 15),
        ("H", "Projekti päättyy", "_endDate", 15),
        ("I", "Osoite", "streetAddress", 30),
        ("J", "Postinumero", "postalCode", 12),
        ("K", "Vastuuhenkilö", "responsiblePerson", 25),
        ("L", "Palveluluokka", "_serviceCode", 15),
        ("M", "Käyttöomaisuusluokka", "_assetComponent", 20),
        ("N", "Profiilin nimi", "profileName", 30),
        ("O", "Pitoaika", "_holdingPeriod", 10),
        ("P", "Invest. profiili", "investmentProfile", 15),
        ("Q", "Valmius", "readiness", 10),
        ("R", "Yksikkö", "unit", 10),
    ]

    HEADER_STYLE = {
        "font": Font(bold=True, size=11),
        "fill": PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid"),
        "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
    }

    CELL_STYLE = {
        "alignment": Alignment(horizontal="left", vertical="center"),
        "border": Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        ),
    }

    def _get_value(self, opening, field: str) -> str:
        if field.startswith("_"):
            return self._get_computed(opening, field)
        value = getattr(opening, field, None)
        return str(value) if value is not None else ""

    def _get_computed(self, opening, field: str) -> str:
        if field == "_numberRange" and opening.projectNumberRange:
            r = opening.projectNumberRange
            return f"{r.rangeStart} - {r.rangeEnd}"
        if field == "_typeCode" and opening.projectType:
            return opening.projectType.code or ""
        if field == "_typePriority" and opening.projectType:
            return opening.projectType.priority or ""
        if field == "_startDate" and opening.projectStartDate:
            return opening.projectStartDate.strftime("%d.%m.%Y")
        if field == "_endDate" and opening.projectEndDate:
            return opening.projectEndDate.strftime("%d.%m.%Y")
        if field == "_serviceCode" and opening.serviceClass:
            return opening.serviceClass.code or ""
        if field == "_assetComponent" and opening.assetClass:
            return opening.assetClass.componentClass or ""
        if field == "_holdingPeriod" and opening.assetClass:
            years = opening.assetClass.holdingPeriodYears
            return str(years) if years else ""
        return ""

    def generate_excel(self, opening) -> BytesIO:
        return self.generate_batch_excel([opening])

    def generate_batch_excel(self, openings: List) -> BytesIO:
        wb = Workbook()
        ws = wb.active
        ws.title = "Projektin avauslomake"

        for col, header, _, width in self.COLUMNS:
            cell = ws[f"{col}1"]
            cell.value = header
            cell.font = self.HEADER_STYLE["font"]
            cell.fill = self.HEADER_STYLE["fill"]
            cell.alignment = self.HEADER_STYLE["alignment"]
            cell.border = self.CELL_STYLE["border"]
            ws.column_dimensions[col].width = width

        ws.row_dimensions[1].height = 30

        for row, opening in enumerate(openings, start=2):
            for col, _, field, _ in self.COLUMNS:
                cell = ws[f"{col}{row}"]
                cell.value = self._get_value(opening, field)
                cell.alignment = self.CELL_STYLE["alignment"]
                cell.border = self.CELL_STYLE["border"]

        ws.freeze_panes = "A2"

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def get_filename(self, opening) -> str:
        if opening.project and opening.project.name:
            name = opening.project.name
            safe_name = "".join(c for c in name if c.isalnum() or c in " -_")[:50]
            return f"talpa_avauslomake_{safe_name}.xlsx"
        return f"talpa_avauslomake_{opening.id}.xlsx"
