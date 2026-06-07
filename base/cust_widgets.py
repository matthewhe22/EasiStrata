from django.forms.widgets import Widget, FileInput, DateInput


class FileInputCustom(FileInput):
    template_name = 'base/file_custom.html'


class FengyuanChenDatePickerInput(DateInput, Widget):
    template_name = 'base/fengyuanchen_datepicker.html'


class DateTimePicker(Widget):
    template_name = 'base/datetimepicker.html'
