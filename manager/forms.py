from django import forms

class ImportForm(forms.Form):
    upload_csv = forms.FileField(label="CSV file", help_text="", required=True)
    calendar_choices = forms.ChoiceField(choices=[])

    upload_csv.widget.attrs.update({'class': 'form-control-file'})
    calendar_choices.widget.attrs.update({'class': 'form-control'})

    def __init__(self, *args, **kwargs):
        my_arg = kwargs.pop('my_arg')
        super().__init__(*args,**kwargs)
        self.fields['calendar_choices'].choices = my_arg

class ExportForm(forms.Form):
    calendar_choices = forms.ChoiceField(choices=[], required=False, label="")
    timeMin = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'], label="From ")
    timeMax = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'], label="Until ")

    def __init__(self, *args, **kwargs):
        my_arg = kwargs.pop('my_arg')
        super().__init__(*args,**kwargs)
        self.fields['calendar_choices'].choices = my_arg
