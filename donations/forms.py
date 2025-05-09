from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Customer, Notification
from donations.models import Sahyog, SahyogReceipt, VyawasthaShulkReceipt, AccountDetails
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser  # Import your custom user model




from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2', 'role')  # ✅ Removed 'username'


class CustomerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'gender', 'dob', 'mobile',
            'department', 'post', 'transaction_id', 'home_address',
            'payment_slip'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_slip': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'post': forms.TextInput(attrs={'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }




class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name", "email", "mobile", "mobile_home", "dob", "gender",
            "first_nominee_name", "first_nominee_relation", "first_nominee_mobile", 
            "department", "post", "posting_state", "posting_district", "home_address","disease","transaction_id","home_district",
            "payment_slip", "approved"
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "posting_state": forms.TextInput(attrs={"class": "form-control"}),
            "posting_district": forms.TextInput(attrs={"class": "form-control"}),
            "home_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "payment_slip": forms.FileInput(attrs={"class": "form-control"}),
            "transaction_id": forms.TextInput(attrs={"class": "form-control"}),
            "approved": forms.Select(choices=[(True, "Approved"), (False, "Pending")], attrs={"class": "form-control"}),
            # ✅ Add Nominee Details Styling
            "first_nominee_name": forms.TextInput(attrs={"class": "form-control"}),
            "first_nominee_relation": forms.TextInput(attrs={"class": "form-control"}),
            "first_nominee_mobile": forms.TextInput(attrs={"class": "form-control"}),
        }





class SahyogForm(forms.ModelForm):
    class Meta:
        model = Sahyog
        fields = ['title', 'account_holder_name', 'bank_name', 'account_number', 'ifsc_code', 'qr_code']


class SahyogReceiptForm(forms.ModelForm):
    class Meta:
        model = SahyogReceipt
        fields = ['receipt_image']  # ✅ Removed sahyog






from django import forms
from .models import VyawasthaShulkReceipt, AccountDetails

class VyawasthaShulkReceiptForm(forms.ModelForm):
    account_holder_name = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    account_number = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    ifsc_code = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    bank_name = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    branch = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = VyawasthaShulkReceipt
        fields = ["receipt_image", "amount", "transaction_id", "payment_date"]

    def __init__(self, *args, **kwargs):
        super(VyawasthaShulkReceiptForm, self).__init__(*args, **kwargs)
        account = AccountDetails.objects.first()

        if account:
            self.fields["account_holder_name"].initial = account.account_holder_name
            self.fields["account_number"].initial = account.account_number
            self.fields["ifsc_code"].initial = account.ifsc_code
            self.fields["bank_name"].initial = account.bank_name
            self.fields["branch"].initial = account.branch







class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["title", "message", "target_type"]

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data.get("target_type")
        specific_user = self.data.get("specific_user")

        if target_type == "specific_user" and not specific_user:
            raise forms.ValidationError("Please select a user for a specific notification.")
        
        return cleaned_data






from .models import BloodDonation

class BloodDonationForm(forms.ModelForm):
    class Meta:
        model = BloodDonation
        fields = ["name", "blood_group", "contact", "last_donation_date", "category", "self_declaration"]

class BloodDonationApprovalForm(forms.ModelForm):
    class Meta:
        model = BloodDonation
        fields = ["status"]
