from django import forms
from .models import Subject, Major, MidtermExam, Group


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
        fields = ['subject', 'group', 'questions', 'due_date', 'time_limit']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 180
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'questions': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
        }
        labels = {
            'subject': 'Առարկա',
            'group': 'Խումբ',
            'questions': 'Հարցեր',
            'due_date': 'Ավարտի ամսաթիվ և ժամ',
            'time_limit': 'Քննության տևողություն (րոպե)'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['subject'].queryset = Subject.objects.filter(lecturers=user)
            self.fields['group'].queryset = Group.objects.filter(
                major__in=self.fields['subject'].queryset.values('major')
            )