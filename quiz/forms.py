from django import forms
from .models import Subject, Major, MidtermExam


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


class MidtermExamForm(forms.ModelForm):
    class Meta:
        model = MidtermExam
        fields = ['subject', 'group', 'questions','due_date', 'time_limit']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'questions': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # user-ը ստանում ենք view-ից
        super().__init__(*args, **kwargs)

        if user is not None:
            # Ֆիլտրենք subject-ը՝ ըստ դասախոսի
            self.fields['subject'].queryset = Subject.objects.filter(lecturers=user)