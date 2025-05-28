from django import forms
from .models import Subject, Major, MidtermExam, Group,Feedback, TestQuestion


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
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    questions_per_student = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        initial=6,
        label='Number of Questions per Student',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

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

        # Optional: filter subjects based on lecturer
        if user and hasattr(user, 'is_lecturer') and user.is_lecturer:
            self.fields['subject'].queryset = Subject.objects.filter(lecturer=user)

        self.fields['questions'].required = False  # Important

        subject_id = None
        if self.data.get('subject'):
            subject_id = self.data.get('subject')
        elif self.initial.get('subject'):
            subject_id = self.initial.get('subject')
        elif self.instance and self.instance.pk:
            subject_id = self.instance.subject_id

        if subject_id:
            self.fields['questions'].queryset = TestQuestion.objects.filter(subject_id=subject_id)
        else:
            self.fields['questions'].queryset = TestQuestion.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        use_random = cleaned_data.get('use_random')
        questions_per_student = cleaned_data.get('questions_per_student')
        subject_id = cleaned_data.get('subject')

        if use_random:
            if not questions_per_student:
                raise forms.ValidationError("Please specify number of questions when using random selection")

            if subject_id:
                available_questions = TestQuestion.objects.filter(subject_id=subject_id).count()
                if questions_per_student > available_questions:
                    raise forms.ValidationError(
                        f"Only {available_questions} questions available for the selected subject."
                    )
        else:
            if not cleaned_data.get('questions'):
                raise forms.ValidationError("Please select questions or enable random selection")

        return cleaned_data


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'name', 'email', 'subject', 'message', 'urgency']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }