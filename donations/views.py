from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from .forms import CustomerRegistrationForm, NotificationForm, BloodDonationApprovalForm, BloodDonationForm
from .models import Customer, BloodDonation
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.contrib import messages
from .models import Customer, Notification, VyawasthaShulkReceipt
from .models import CustomUser, Sahyog
from .forms import CustomUserCreationForm, SahyogForm, SahyogReceipt, VyawasthaShulkReceiptForm
from donations.forms import SahyogReceiptForm
import os
from datetime import datetime
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth import get_user_model
import os







User = get_user_model()  # Get correct User model

def admin_dashboard(request):
    total_users = User.objects.count()
    total_sahyog = Sahyog.objects.count()
    total_blood_donors = BloodDonation.objects.count()
    total_vyawastha_shulk = VyawasthaShulkReceipt.objects.count()

    # Print values in the terminal
    print("DEBUG - Total Users:", total_users)
    print("DEBUG - Total Sahyog:", total_sahyog)
    print("DEBUG - Total Blood Donors:", total_blood_donors)
    print("DEBUG - Total Vyawastha Shulk:", total_vyawastha_shulk)

    context = {
        "total_users": total_users,
        "total_sahyog": total_sahyog,
        "total_blood_donors": total_blood_donors,
        "total_vyawastha_shulk": total_vyawastha_shulk,
    }
    return render(request, "donations/admin_dashboard.html", context)



from django.db.models import Q

CustomUser = get_user_model()

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("username")  # ✅ Users enter email, but Django expects 'username'
        password = request.POST.get("password")

        print(f"🔍 Debug: Login Email = {email}, Password = {password}")

        # ✅ Find user by email
        user = CustomUser.objects.filter(email=email).first()

        if not user:
            print("❌ Debug: No user found with this email")
            return render(request, "donation/login.html", {"error": "Invalid email or password"})

        print(f"✅ Debug: Found user with email = {user.email}")

        # ✅ Authenticate using 'username' argument (Django expects username, not email)
        user = authenticate(request, username=email, password=password)

        if user is None:
            print("❌ Debug: Authentication failed, incorrect password")
            return render(request, "donation/login.html", {"error": "Invalid email or password"})

        print(f"✅ Debug: Authentication successful for {user.email}")

        login(request, user)

        return redirect("admin_dashboard" if user.is_staff else "user_dashboard")

    return render(request, "donation/login.html")



        





def register_customer(request):
    if request.method == "POST":
        try:
            print("✅ Received POST Request!")  # Debugging

            name = request.POST.get("name")
            email = request.POST.get("email")
            mobile = request.POST.get("mobile")
            password = request.POST.get("password")
            dob = request.POST.get("dob")  
            pan = request.POST.get("pan")  
            payment_slip = request.FILES.get("payment_slip")  

            print("✅ Data Received: ", name, email, mobile, dob)  # Debugging

            if not name or not email or not mobile or not password or not dob or not pan:
                return JsonResponse({"success": False, "message": "All fields are required."})
            if not payment_slip:
                return JsonResponse({"success": False, "message": "Payment slip is required."})

            dob = datetime.strptime(dob, "%Y-%m-%d").date()

            # ✅ Check if email is already registered
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({"success": False, "message": "Email already registered."})

            # ✅ Create a user in CustomUser model
            user = CustomUser.objects.create(
                email=email,
                password=make_password(password),  # ✅ Encrypt password  
                role="user",
                is_approved=False,  # ✅ Requires admin approval
                is_active=False  
            )

            # ✅ Create corresponding Customer entry
            customer = Customer.objects.create(
                user=user,  
                name=name,
                email=email,
                mobile=mobile,
                dob=dob,
                pan=pan,
                approved=False,  
                payment_slip=payment_slip  
            )

            print("✅ Customer Saved Successfully!")  

            # ✅ Notify Admin for Approval
            subject = "New User Registration - Pending Approval"
            message = f"""
            A new user has registered on your platform.
            
            Name: {name}
            Email: {email}
            Mobile: {mobile}
            Date of Birth: {dob}
            PAN: {pan}

            Please review their registration details and approve their account.
            """
            admin_email = settings.DEFAULT_FROM_EMAIL  # Use the default admin email
            send_mail(subject, message, admin_email, [admin_email])

            # ✅ Return JSON response for AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Registration successful. Await admin approval."})
            
            # ✅ If accessed normally, redirect to login page
            else:
              return redirect("registration_success")  # ✅ Redirect non-AJAX requests

        except Exception as e:
            print("❌ Error Occurred: ", str(e))  
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"})

    return render(request, "donation/register.html")





@login_required
def approve_user(request, user_id):
    if request.method != "POST":  # ❌ Rejects GET requests
        return JsonResponse({"error": "Invalid request method"}, status=405)

    # ✅ Ensure the user exists
    user = get_object_or_404(CustomUser, id=user_id)

    # ✅ Ensure the customer exists
    customer = Customer.objects.filter(user=user).first()
    if not customer:
        return JsonResponse({"error": "No customer found"}, status=404)

    # ✅ Approve and activate the user
    user.is_approved = True
    user.is_active = True
    user.save()

    # ✅ Approve the customer entry
    customer.approved = True
    customer.save()

    return redirect("manage_members")


@login_required
def reject_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(CustomUser, id=user_id)
        user.delete()  # ✅ Delete user from database
        print(f"❌ User {user.email} has been deleted.")

        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "User deleted successfully!"})

        return redirect("manage_members")  # ✅ Redirect back to admin panel

    return JsonResponse({"success": False, "message": "Invalid request method."})






from django.contrib.auth.backends import ModelBackend


# ✅ Custom authentication backend that supports both email and username
class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # ✅ Allow both email and admin username login
            user = CustomUser.objects.get(email=username) if "@" in username else CustomUser.objects.get(username=username)

            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None

# ✅ Login View (Supports Both Admin & User Login)
def custom_admin_login(request):
    if request.user.is_authenticated:
        return redirect("admin_dashboard" if request.user.role == "admin" else "user_dashboard")

    if request.method == "POST":
        email_or_username = request.POST.get("email")  # ✅ Supports email or username
        password = request.POST.get("password")
        user = authenticate(request, username=email_or_username, password=password)

        if user:
            if user.is_approved and user.is_active:
                login(request, user)
                return redirect("admin_dashboard" if user.role == "admin" else "user_dashboard")
            else:
                messages.error(request, "Your account is pending approval or inactive.")
        else:
            messages.error(request, "Invalid email/username or password.")

    return render(request, "donation/login.html")









from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@csrf_exempt  # Bypasses CSRF token issues (for GET logout)
def user_logout(request):
    if request.method == "POST" or request.method == "GET":  # Accept both methods
        logout(request)
        return redirect("login")  # Redirect to login page







def generate_payment_receipt(request, customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return HttpResponse("Customer not found", status=404)

    # Set up the response as a PDF file
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Payment_Receipt_{customer.md_code}.pdf"'

    # Create the PDF object
    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle(f"Payment Receipt - {customer.md_code}")

    # Add content to the PDF
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Payment Receipt")
    pdf.setFont("Helvetica", 12)

    pdf.drawString(100, 700, f"MD Code: {customer.md_code}")
    pdf.drawString(100, 680, f"Name: {customer.name}")
    pdf.drawString(100, 660, f"Email: {customer.email}")
    pdf.drawString(100, 640, f"Mobile: {customer.mobile}")
    pdf.drawString(100, 620, f"Nominee: {customer.nominee_name} ({customer.nominee_relation})")
    pdf.drawString(100, 600, f"Payment Slip: {customer.payment_slip.url if customer.payment_slip else 'N/A'}")

    pdf.drawString(100, 570, "Thank you for your payment!")

    pdf.showPage()
    pdf.save()

    return response




# ✅ Admin Dashboard (Only for Custom Admin)
@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect('user_dashboard')  # If user is not admin, redirect to user dashboard
    return render(request, "donation/admin_dashboard.html")

# ✅ User Dashboard (For Normal Users)
@login_required
def user_dashboard(request):
    if request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to access this page.")
    return render(request, "donation/user_dashboard.html")





def manage_members(request):
    approved_users = Customer.objects.filter(approved=True)
    pending_requests = Customer.objects.filter(approved=False)

    return render(request, "donation/manage_members.html", {
        "approved_users": approved_users,
        "pending_requests": pending_requests
    })







@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_user(request, user_id):
    customer = get_object_or_404(Customer, id=user_id)
    customer.delete()  # ❌ Rejecting user will remove them

    return JsonResponse({"message": f"{customer.name} has been rejected and removed."})





@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_member(request, user_id):
    customer = get_object_or_404(Customer, id=user_id)

    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.email = request.POST.get("email")
        customer.mobile = request.POST.get("mobile")
        customer.department = request.POST.get("department")
        customer.save()
        messages.success(request, "Member details updated successfully.")
        return redirect('manage_members')

    return render(request, "donation/edit_member.html", {"customer": customer})




@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_member(request, user_id):
    customer = get_object_or_404(Customer, id=user_id)
    customer.delete()
    return JsonResponse({"message": "Member deleted successfully."})



@login_required
@user_passes_test(lambda u: u.is_staff)
def add_member(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = True  # Automatically approve admin-created members
            user.is_active = True
            user.save()
            messages.success(request, "New member added successfully.")
            return redirect('manage_members')
    else:
        form = CustomUserCreationForm()
    return render(request, 'donation/add_member.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def running_sahyog(request):
    if request.method == "POST":
        title = request.POST.get("title")
        account_holder_name = request.POST.get("account_holder_name")  # ✅ New Field
        bank_name = request.POST.get("bank_name")
        account_number = request.POST.get("account_number")
        ifsc_code = request.POST.get("ifsc_code")
        qr_code = request.FILES.get("qr_code")

        sahyog = Sahyog(
            title=title,
            account_holder_name=account_holder_name,  # ✅ Saving New Field
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            qr_code=qr_code
        )
        sahyog.save()
        return redirect('sahyog_list')

    return render(request, "donation/running_sahyog.html")



# ✅ Restrict Editing to Custom Admins Only
@login_required
@user_passes_test(lambda u: u.is_staff)  # ✅ Only Custom Admin can access
def edit_sahyog(request, sahyog_id):
    sahyog = get_object_or_404(Sahyog, id=sahyog_id)  # Get Sahyog by ID

    if request.method == "POST":
        form = SahyogForm(request.POST, request.FILES, instance=sahyog)
        if form.is_valid():
            form.save()
            return redirect('sahyog_list')  # Redirect to Sahyog list after edit
    else:
        form = SahyogForm(instance=sahyog)

    return render(request, "donation/edit_sahyog.html", {"form": form, "sahyog": sahyog})


# ✅ Restrict Deleting to Custom Admins Only
@login_required
@user_passes_test(lambda u: u.is_staff)  # Only admins can delete
def delete_sahyog(request, sahyog_id):
    sahyog = get_object_or_404(Sahyog, id=sahyog_id)
    sahyog.delete()
    return redirect('sahyog_list')



def sahyog_list(request):
    sahyog_entries = Sahyog.objects.all()  # ✅ Get all Sahyog entries
    
    # ✅ Choose base template dynamically
    base_template = "donation/base.html" if request.user.is_staff else "donation/base_user.html"
    
    return render(request, "donation/sahyog_list.html", {
        "sahyog_list": sahyog_entries,
        "base_template": base_template
    })







# Check if the user is a Custom Admin
def is_custom_admin(user):
    return user.is_staff  # Modify if you have a separate admin role

# ✅ View to send notifications (only for Custom Admin)
@staff_member_required
def send_notification(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            recipient = form.cleaned_data["recipient"]

            if recipient:
                notification.sender = request.user
                notification.save()
            else:
                # Send to all users
                users = CustomUser.objects.filter(role="user")
                for user in users:
                    Notification.objects.create(
                        sender=request.user,
                        message=notification.message
                    )

            return redirect("send_notification")  # Redirect after sending
    else:
        form = NotificationForm()

    return render(request, "donation/send_notification.html", {"form": form})

# ✅ View to display notifications for admin
@login_required
@user_passes_test(is_custom_admin)
def manage_notifications(request):
    notifications = Notification.objects.order_by("-created_at")  # Show latest notifications first
    return render(request, "donation/manage_notifications.html", {"notifications": notifications})


@staff_member_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return redirect("manage_notifications")  # Redirect back to notifications list



def user_dashboard(request):
    notifications = Notification.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'donation/user_dashboard.html', {'notifications': notifications})

















from django.contrib.auth.decorators import login_required

@login_required
def user_dashboard(request):
    return render(request, 'donation/user_dashboard.html', {'user': request.user})




@login_required
def user_profile(request):
    try:
        customer, created = Customer.objects.get_or_create(user=request.user)  # ✅ Ensure Profile Exists
    except Customer.DoesNotExist:
        messages.error(request, "No profile data found. Please contact support.")
        return redirect("user_dashboard")

    if request.method == "POST":
        customer.name = request.POST.get("name", customer.name)
        customer.mobile = request.POST.get("mobile", customer.mobile)
        customer.email = request.POST.get("email", customer.email)
        customer.dob = request.POST.get("dob", customer.dob)
        customer.pan = request.POST.get("pan", customer.pan)
        customer.home_address = request.POST.get("home_address", customer.home_address)
        customer.department = request.POST.get("department", customer.department)
        customer.post = request.POST.get("post", customer.post)
        customer.posting_district = request.POST.get("posting_district", customer.posting_district)
        customer.posting_block = request.POST.get("posting_block", customer.posting_block)
        customer.disease = request.POST.get("disease", customer.disease)
        customer.cause_of_illness = request.POST.get("cause_of_illness", customer.cause_of_illness)

        # ✅ Save Nominee Details
        customer.first_nominee_name = request.POST.get("first_nominee_name", customer.first_nominee_name)
        customer.first_nominee_relation = request.POST.get("first_nominee_relation", customer.first_nominee_relation)
        customer.first_nominee_mobile = request.POST.get("first_nominee_mobile", customer.first_nominee_mobile)

        customer.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("user_profile")

    return render(request, "donation/user_profile.html", {"customer": customer})



@login_required
def upload_receipt(request):
    if request.method == "POST":
        form = SahyogReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user  # Attach the receipt to the logged-in user
            receipt.sahyog = None  # ✅ Ensure no Sahyog is assigned
            receipt.save()
            return redirect("user_receipts")  # Redirect to receipt list

    else:
        form = SahyogReceiptForm()

    return render(request, "donation/upload_receipt.html", {"form": form})




@login_required
def user_receipts(request):
    receipts = SahyogReceipt.objects.filter(user=request.user)
    return render(request, "donation/user_receipts.html", {"receipts": receipts})
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_receipts(request):
    receipts = SahyogReceipt.objects.all()
    return render(request, "donation/admin_receipts.html", {"receipts": receipts})




@login_required
def upload_vyawastha_shulk(request):
    if request.method == "POST":
        form = VyawasthaShulkReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user
            receipt.save()
            return redirect("user_vyawastha_shulk_receipts")  # Redirect to receipt list

    else:
        form = VyawasthaShulkReceiptForm()

    return render(request, "donation/upload_vyawastha_shulk.html", {"form": form})



@login_required
def user_vyawastha_shulk_receipts(request):
    receipts = VyawasthaShulkReceipt.objects.filter(user=request.user)
    return render(request, "donation/user_vyawastha_shulk_receipts.html", {"receipts": receipts})





@staff_member_required
def admin_vyawastha_shulk_receipts(request):
    receipts = VyawasthaShulkReceipt.objects.all()
    return render(request, "donation/admin_vyawastha_shulk_receipts.html", {"receipts": receipts})





def user_dashboard(request):
    notifications = Notification.objects.filter(is_active=True).order_by("-created_at")
    return render(request, "donation/user_dashboard.html", {"notifications": notifications})






@login_required
def submit_blood_donation(request):
    if request.method == "POST":
        form = BloodDonationForm(request.POST, request.FILES)
        if form.is_valid():
            blood_donation = form.save(commit=False)
            blood_donation.user = request.user
            blood_donation.save()
            return redirect("blood_donation_list")
    else:
        form = BloodDonationForm()
    return render(request, "donation/blood_donation_form.html", {"form": form})


@login_required
def blood_donation_list(request):
    donations = BloodDonation.objects.all().order_by("-created_at")
    
    # Use different base templates based on user type
    if request.user.is_staff:
        base_template = "donation/base.html"
    else:
        base_template = "donation/base_user.html"

    return render(request, "donation/blood_donation_list.html", {
        "donations": donations,
        "base_template": base_template
    })





@staff_member_required
def update_blood_donation_status(request, donation_id, status):
    donation = get_object_or_404(BloodDonation, id=donation_id)
    if status in ["Pending", "Approved", "Completed"]:
        donation.status = status
        donation.save()
    return redirect("blood_donation_list")