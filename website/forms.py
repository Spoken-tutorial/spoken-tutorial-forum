from django import forms

from spoken_auth.models import TutorialDetails, TutorialResources, FossCategory
from django.db.models import Q
tutorials = (
    ("Select a Tutorial", "Select a Tutorial"),
)
minutes = ()
seconds = ()


def _get_category_choices():
    """Distinct FOSS categories for new-question form, sorted alphabetically."""
    categories = list(
        TutorialResources.objects.filter(
            Q(status=1) | Q(status=2),
            language__name='English',
            tutorial_detail__foss__show_on_homepage=1,
        )
        .values_list('tutorial_detail__foss__foss', flat=True)
        .distinct()
    )
    # Remove empty/None and sort case-insensitively (A-Z)
    categories = [c for c in categories if c]
    categories = sorted(set(categories), key=lambda x: x.lower())
    return [('', 'Select a Category')] + [(c, c) for c in categories]


class NewQuestionForm(forms.Form):
    category = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={}),
        required=True,
        error_messages={'required': 'State field is required.'},
    )
    title = forms.CharField(max_length=200)
    body = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        # Values that can be passed explicitly (e.g. from the spoken website)
        category = kwargs.pop('category', None)
        selecttutorial = kwargs.pop('tutorial', None)
        select_min = kwargs.pop('minute_range', None)
        select_sec = kwargs.pop('second_range', None)

        super(NewQuestionForm, self).__init__(*args, **kwargs)
        self.fields['category'].choices = _get_category_choices()
        tutorial_choices = (
            ("Select a Tutorial", "Select a Tutorial"),
        )

        # If no explicit minute/second values were provided (e.g. normal POST),
        # preserve any values that came from submitted form data so that
        # validation errors (like missing reCAPTCHA) do not wipe them out.
        data = args[0] if args else {}
        if select_min is None and data and 'minute_range' in data:
            select_min = data.get('minute_range')
        if select_sec is None and data and 'second_range' in data:
            select_sec = data.get('second_range')

        # When a minute/second value is available (from the spoken website or a
        # previous form submission), show that value as the only selectable
        # option; otherwise show the default placeholders.
        if select_min:
            minutes = (
                (select_min, select_min),
            )
        else:
            minutes = (
                ("", "min"),
            )

        if select_sec:
            seconds = (
                (select_sec, select_sec),
            )
        else:
            seconds = (
                ("", "sec"),
            )

        if not category and args and 'category' in args[0] and args[0]['category']:
            category = args[0]['category']
        if FossCategory.objects.filter(foss=category).exists():
            self.fields['category'].initial = category
            tutorials = TutorialDetails.objects.using('spoken').filter(
                foss__foss=category
            ).order_by('level', 'order')
            for tutorial in tutorials:
                tutorial_choices += ((tutorial.tutorial, tutorial.tutorial),)
            self.fields['tutorial'] = forms.CharField(widget=forms.Select(choices=tutorial_choices))
            if TutorialDetails.objects.using('spoken').filter(tutorial=selecttutorial).exists():
                self.fields['tutorial'].initial = selecttutorial

                self.fields['minute_range'] = forms.CharField(widget=forms.Select(choices=minutes))
                self.fields['second_range'] = forms.CharField(widget=forms.Select(choices=seconds))
            else:
                self.fields['minute_range'] = forms.CharField(widget=forms.Select(choices=minutes))
                self.fields['second_range'] = forms.CharField(widget=forms.Select(choices=seconds))
        else:
            self.fields['tutorial'] = forms.CharField(widget=forms.Select(choices=tutorial_choices))
            self.fields['minute_range'] = forms.CharField(widget=forms.Select(choices=minutes))
            self.fields['second_range'] = forms.CharField(widget=forms.Select(choices=seconds))


class AnswerQuesitionForm(forms.Form):
    question = forms.IntegerField(widget=forms.HiddenInput())
    body = forms.CharField(widget=forms.Textarea())
