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
            'name', 'email', 'gender', 'dob', 'mobile', 'mobile_home', 'pan',
            'department', 'post', 'posting_district', 'posting_block',
            'home_address', 'home_district', 'disease', 'cause_of_illness',
            'payment_slip'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_slip': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'post': forms.TextInput(attrs={'class': 'form-control'}),
            'posting_district': forms.TextInput(attrs={'class': 'form-control'}),
            'posting_block': forms.TextInput(attrs={'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cause_of_illness': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
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
    recipient = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role="user"), 
        required=False, 
        empty_label="All Users"
    )  # Allows admin to send to one user or all

    class Meta:
        model = Notification
        fields = ["recipient", "message"]





from .models import BloodDonation

class BloodDonationForm(forms.ModelForm):
    class Meta:
        model = BloodDonation
        fields = ["name", "blood_group", "contact", "last_donation_date", "category", "self_declaration"]

class BloodDonationApprovalForm(forms.ModelForm):
    class Meta:
        model = BloodDonation
        fields = ["status"]
