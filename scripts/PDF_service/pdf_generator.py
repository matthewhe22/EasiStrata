from PyPDF2 import PdfFileMerger

from my_project import settings


def merge_pdf_files(pdf_path_list, file_name, upload_to="AGM/"):
    merger = PdfFileMerger()

    for pdf in pdf_path_list:
        merger.append(pdf)

    output_path = settings.MEDIA_ROOT + '/' + upload_to + file_name

    merger.write(output_path)
    merger.close()
    return upload_to + file_name
