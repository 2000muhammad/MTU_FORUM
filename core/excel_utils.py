from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
import html
import re
import xml.etree.ElementTree as ET


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""


def column_name(index):
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def column_index(cell_ref):
    letters = re.match(r"([A-Z]+)", cell_ref or "")
    if not letters:
        return 1
    index = 0
    for char in letters.group(1):
        index = index * 26 + ord(char) - 64
    return index


def build_xlsx(headers, rows):
    sheet_rows = [headers, *rows]
    xml_rows = []
    for row_index, row in enumerate(sheet_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            value = "" if value is None else str(value)
            ref = f"{column_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(value)}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    width_xml = "".join(f'<col min="{i}" max="{i}" width="24" customWidth="1"/>' for i in range(1, len(headers) + 1))
    sheet = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>{width_xml}</cols>
  <sheetData>{''.join(xml_rows)}</sheetData>
</worksheet>"""

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    output.seek(0)
    return output.getvalue()


def parse_xlsx(file_obj):
    with ZipFile(file_obj) as archive:
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for item in root.findall("x:si", ns):
                shared_strings.append("".join(node.text or "" for node in item.findall(".//x:t", ns)))

        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = []
        for row in sheet.findall(".//x:row", ns):
            values = []
            for cell in row.findall("x:c", ns):
                target_index = column_index(cell.attrib.get("r")) - 1
                while len(values) < target_index:
                    values.append("")
                cell_type = cell.attrib.get("t")
                if cell_type == "inlineStr":
                    values.append("".join(node.text or "" for node in cell.findall(".//x:t", ns)).strip())
                else:
                    raw = cell.findtext("x:v", default="", namespaces=ns)
                    if cell_type == "s" and raw:
                        values.append(shared_strings[int(raw)].strip())
                    else:
                        values.append(raw.strip())
            rows.append(values)
    if not rows:
        return []
    headers = [value.strip().lower() for value in rows[0]]
    return [dict(zip(headers, row)) for row in rows[1:] if any(str(value).strip() for value in row)]


def truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "да", "активно", "active", "required"}
