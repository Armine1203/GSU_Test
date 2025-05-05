from django import forms
from .models import Subject, Major


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'major', 'course', 'year', 'semester']
        widgets = {
            'year': forms.NumberInput(attrs={'min': 2020, 'max': 2030}),
            'course': forms.NumberInput(attrs={'min': 1, 'max': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['major'].queryset = Major.objects.all()