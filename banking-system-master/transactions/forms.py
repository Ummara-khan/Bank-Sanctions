# forms.py

from django import forms
from .models import NameVariation  # Make sure this path is correct

class UploadFileForm(forms.Form):
    ofac_file = forms.FileField(required=False)
    un_file = forms.FileField(required=False)
    eu_file = forms.FileField(required=False)


from django import forms
from .models import NameVariation

class NameVariationForm(forms.ModelForm):
    class Meta:
        model = NameVariation
        fields = ['variation', 'score', 'is_active']

class DisableNameVariationForm(forms.ModelForm):
    class Meta:
        model = NameVariation
        fields = ['is_active']
        widgets = {
            'is_active': forms.HiddenInput()
        }

from django import forms
from .models import NameVariation

class NameVariationForm(forms.ModelForm):
    class Meta:
        model = NameVariation
        fields = ['variation', 'score', 'is_active']
