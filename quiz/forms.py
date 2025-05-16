from django import forms
from .models import Subject, Major, MidtermExam, Group,Feedback


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
    use_random = forms.BooleanField(
        required=False,
        label='Use Random Question Selection',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    questions_per_student = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        initial=6,
        label='Number of Questions per Student',
        widget=forms.NumberInput(attrs={'class': 'form-control'}))

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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['subject'].queryset = Subject.objects.filter(lecturers=user)
            self.fields['group'].queryset = Group.objects.filter(
                major__in=self.fields['subject'].queryset.values('major')
            )

        # Make questions field not required since we might use random selection
        self.fields['questions'].required = False

    def clean(self):
        cleaned_data = super().clean()
        use_random = cleaned_data.get('use_random')
        questions_per_student = cleaned_data.get('questions_per_student')

        if use_random and not questions_per_student:
            raise forms.ValidationError("Please specify number of questions when using random selection")

        if not use_random and not cleaned_data.get('questions'):
            raise forms.ValidationError("Please select questions or enable random selection")

        return cleaned_data

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'name', 'email', 'subject', 'message', 'urgency']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }