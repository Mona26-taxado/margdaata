
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password


# ✅ Custom User Model (Only One Definition)
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Custom Admin'),
        ('user', 'User'),
    ]
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)  # Allow blank usernames
    email = models.EmailField(unique=True)  # Email is required and unique
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_approved = models.BooleanField(default=False)  # Approval field

    USERNAME_FIELD = "email"  # ✅ Use email instead of username for login
    REQUIRED_FIELDS = []  # No extra required fields

    # ✅ Fixing group and permission conflicts
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.username:  # Auto-generate username if blank
            self.username = self.email
        super().save(*args, **kwargs)


# ✅ Customer Model (Linked to CustomUser)
class Customer(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True  
    )
    name = models.CharField(max_length=100)
    md_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    email = models.EmailField(unique=True)
    gender_choices = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    gender = models.CharField(max_length=10, choices=gender_choices)
    dob = models.DateField(null=True)
    mobile = models.CharField(max_length=15, unique=True)
    mobile_home = models.CharField(max_length=15, blank=True, null=True)
    aadhar = models.CharField(max_length=12, unique=True, blank=False, null=False)

    # ✅ Nominee Details
    first_nominee_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Exists
    first_nominee_relation = models.CharField(max_length=100, null=True, blank=True)  # ✅ Must exist
    first_nominee_mobile = models.CharField(max_length=15, null=True, blank=True)

    # ✅ Other Details
    department = models.CharField(max_length=100, null=True, blank=True)
    post = models.CharField(max_length=100, null=True, blank=True)
    posting_state = models.CharField(max_length=100, null=True, blank=True)
    posting_district = models.CharField(max_length=100, null=True, blank=True)
    home_address = models.TextField()
    home_district = models.CharField(max_length=100)
    disease = models.CharField(max_length=100, blank=True, null=True)
    cause_of_illness = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    # ✅ Payment Slip Upload
    payment_slip = models.FileField(upload_to='payment_slips/', blank=False, null=False)

    # ✅ Fix Password Storage (Use Hashed Passwords)
    password = models.CharField(max_length=255, blank=True, null=True)

    approved = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.md_code:
            import uuid
            self.md_code = "MD" + str(uuid.uuid4().int)[:6]

        # ✅ Ensure password is hashed before saving
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)

        super(Customer, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.md_code})"







# ✅ Sahyog Model
class Sahyog(models.Model):
    title = models.CharField(max_length=200)
    account_holder_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    qr_code = models.ImageField(upload_to='qr_codes/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ✅ SahyogReceipt Model (Fix `username` Issue)
class SahyogReceipt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sahyog = models.ForeignKey('Sahyog', on_delete=models.SET_NULL, null=True, blank=True)
    receipt_image = models.ImageField(upload_to="sahyog_receipts/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt uploaded by {self.user.email}"  # ✅ Use email instead of username


# ✅ Notification Model
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the custom User model dynamically

class Notification(models.Model):
    TARGET_CHOICES = [
        ("all_users", "All Users"),
        ("specific_user", "Specific User"),
    ]

    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()  # No need to specify charset in Django, just ensure DB supports utf8mb4
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default="all_users")
    specific_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.get_target_type_display()}"



# ✅ VyawasthaShulkReceipt Model
class VyawasthaShulkReceipt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_holder_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=200)
    branch = models.CharField(max_length=200)
    receipt_image = models.ImageField(upload_to="vyawastha_shulk_receipts/")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    payment_date = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt by {self.user.email} - {self.amount} INR"  # ✅ Use email


# ✅ AccountDetails Model
class AccountDetails(models.Model):
    account_holder_name = models.CharField(max_length=200, default="MARGDATA TRUST")
    account_number = models.CharField(max_length=50, default="43861858721")
    ifsc_code = models.CharField(max_length=20, default="SBIN0000125")
    bank_name = models.CharField(max_length=200, default="STATE BANK OF INDIA")
    branch = models.CharField(max_length=200, default="LUCKNOW MAIN BRANCH")

    def __str__(self):
        return f"{self.account_holder_name} - {self.bank_name}"


# ✅ BloodDonation Model
CATEGORY_CHOICES = [
    ("Blood Exchange Participant", "Blood Exchange Participant"),
    ("Donor", "Donor"),
    ("Recipient", "Recipient"),
    ("Dual Participant", "Dual Participant"),
]

STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Approved", "Approved"),
    ("Rejected", "Rejected"),
]

class BloodDonation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    blood_group = models.CharField(max_length=5)
    contact = models.CharField(max_length=15)
    last_donation_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    self_declaration = models.FileField(upload_to="declarations/", null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.category} ({self.status})"
