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
import fitz  # PyMuPDF
from django.http import FileResponse, HttpResponse
from io import BytesIO


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



        




from django.contrib import messages  # ✅ Import messages for Bootstrap alerts

def register_customer(request):
    if request.method == "POST":
        try:
            print("✅ Received POST Request!")  # Debugging

            name = request.POST.get("name")
            email = request.POST.get("email")
            mobile = request.POST.get("mobile")
            password = request.POST.get("password")
            dob = request.POST.get("dob")  
            aadhar = request.POST.get("aadhar")  
            payment_slip = request.FILES.get("payment_slip")  

            if not name or not email or not mobile or not password or not dob or not aadhar:
                messages.error(request, "All fields are required.")
                return redirect("register_customer")  # ✅ Redirect to same page

            if not payment_slip:
                messages.error(request, "Payment slip is required.")
                return redirect("register_customer")

            dob = datetime.strptime(dob, "%Y-%m-%d").date()

            # ✅ Check if email or Aadhar already exists
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect("register_customer")

            if Customer.objects.filter(aadhar=aadhar).exists():
                messages.error(request, "Aadhar number already registered.")
                return redirect("register_customer")

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
                aadhar=aadhar,
                approved=False,  
                payment_slip=payment_slip  
            )

            print("✅ Customer Saved Successfully!")  

            # ✅ Send Admin Notification
            subject = "New User Registration - Pending Approval"
            message = f"""
            A new user has registered on your platform.
            
            Name: {name}
            Email: {email}
            Mobile: {mobile}
            Date of Birth: {dob}
            Aadhar: {aadhar}

            Please review their registration details and approve their account.
            """
            admin_email = settings.DEFAULT_FROM_EMAIL  
            send_mail(subject, message, admin_email, [admin_email])

            # ✅ Success Message
            messages.success(request, "Registration successful! Await admin approval.")
            return redirect("registration_success")  # ✅ Redirect to success page

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect("register_customer")  # ✅ Redirect on error

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






from django.urls import reverse


@login_required
def reject_user(request, user_id):
    if request.method == "POST":
        # ✅ Check if user exists
        user = CustomUser.objects.filter(id=user_id).first()
        if not user:
            messages.error(request, "❌ User not found or already deleted.")
            return redirect(reverse("manage_members"))  # Redirect to members page

        user_email = user.email  # Save email before deleting
        user.delete()

        # ✅ Store success message for Bootstrap alert
        messages.success(request, f"❌ User {user_email} has been rejected and removed.")

        return redirect(reverse("manage_members"))  # Redirect to members page

    messages.error(request, "Invalid request method.")
    return redirect(reverse("manage_members"))




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







from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Customer
from .forms import CustomerRegistrationForm  # Use the existing form

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Customer
from .forms import CustomerEditForm

# View Members: Separate for Admin and Users
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Customer  # Import your model

def view_members(request):
    search_query = request.GET.get('search', '')  # Get search query from request
    approved_users = Customer.objects.filter(approved=True)  # Fetch only approved users

    # If search query exists, filter by name, email, or mobile
    if search_query:
        approved_users = approved_users.filter(
            name__icontains=search_query
        ) | approved_users.filter(
            email__icontains=search_query
        ) | approved_users.filter(
            mobile__icontains=search_query
        )

    # Pagination (10 users per page)
    paginator = Paginator(approved_users, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    approved_users = paginator.get_page(page_number)

    # Check if user is admin or normal user
    if request.user.is_staff:  
        return render(request, "donation/view_members.html", {"approved_users": approved_users, "search_query": search_query})
    else:  
        return render(request, "donation/user_view_members.html", {"approved_users": approved_users, "search_query": search_query})


# Edit Member Details (Only for Admin)
def edit_member(request, user_id):
    if not request.user.is_staff:  # Prevent users from editing
        messages.error(request, "Unauthorized Access!")
        return redirect("view_members")

    member = get_object_or_404(Customer, id=user_id)
    if request.method == "POST":
        form = CustomerEditForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.name}'s details have been updated!")
            return redirect("view_members")
    else:
        form = CustomerEditForm(instance=member)

    return render(request, "donation/edit_member.html", {"form": form, "member": member})

# Delete Member (Only for Admin)
def delete_member(request, user_id):
    if not request.user.is_staff:  # Prevent users from deleting
        messages.error(request, "Unauthorized Access!")
        return redirect("view_members")

    member = get_object_or_404(Customer, id=user_id)
    member.delete()
    messages.error(request, f"{member.name} has been removed!")
    return redirect("view_members")



def user_view_members(request):
    approved_users = Customer.objects.filter(approved=True)
    return render(request, "donation/user_view_members.html", {"approved_users": approved_users})



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





def send_notification(request):
    users = User.objects.all()  # Get all users to show in dropdown
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            target_type = form.cleaned_data["target_type"]
            specific_user = request.POST.get("specific_user")

            if target_type == "specific_user" and not specific_user:
                messages.error(request, "Please select a user.")
            else:
                form.save()
                messages.success(request, "Notification sent successfully!")
                return redirect("send_notification")

    else:
        form = NotificationForm()

    return render(request, "donation/send_notification.html", {"form": form, "users": users})





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
    customer = Customer.objects.filter(user=request.user).first()  # ✅ Fetch existing customer only

    if not customer:
        messages.error(request, "No profile data found. Please contact support.")
        return redirect("user_dashboard")

    if request.method == "POST":
        customer.name = request.POST.get("name") or customer.name
        customer.mobile = request.POST.get("mobile") or customer.mobile
        customer.email = request.POST.get("email") or customer.email
        customer.dob = request.POST.get("dob") or customer.dob
        customer.aadhar = request.POST.get("aadhar") or customer.aadhar
        customer.home_address = request.POST.get("home_address") or customer.home_address
        customer.department = request.POST.get("department") or customer.department
        customer.post = request.POST.get("post") or customer.post
        customer.posting_state = request.POST.get("posting_state") or customer.posting_state
        customer.posting_district = request.POST.get("posting_district") or customer.posting_district
        customer.disease = request.POST.get("disease") or customer.disease
        customer.cause_of_illness = request.POST.get("cause_of_illness") or customer.cause_of_illness

        # ✅ Save Nominee Details
        customer.first_nominee_name = request.POST.get("first_nominee_name") or customer.first_nominee_name
        customer.first_nominee_relation = request.POST.get("first_nominee_relation") or customer.first_nominee_relation
        customer.first_nominee_mobile = request.POST.get("first_nominee_mobile") or customer.first_nominee_mobile

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
    notifications = Notification.objects.all()  # ✅ Fetch all notifications
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









import fitz  # PyMuPDF
from django.http import FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from io import BytesIO
from .models import Customer

@login_required
def generate_id_card(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        return HttpResponse("Customer profile not found", status=404)

    # Load the existing ID Card PDF template
    template_path = "static/assets/img/Margdata_ID_Card.pdf"  # Update with actual file path
    doc = fitz.open(template_path)
    page = doc[0]  # Select the first page

    # Define text positions (X, Y)
    text_positions = {
        "name": (15, 70),  
        "email": (15, 90),
        "mobile": (15, 110),
        "dob": (15, 130),  # ✅ Add DOB
        "posting_state": (15, 150),  # ✅ Add Posting State
        "posting_district": (15, 170),  # ✅ Add Posting District
        "md_code": (15, 190),
        "registered_on": (15, 210),
    }

    # Set font size and color
    font_size = 8  # Increased font size for better readability
    text_color = (0, 0, 0)  # Black
    font_bold = "times-bold"  # Bold font for labels
    font_regular = "times-roman"  # Regular font for values

    # Function to insert text
    def add_text(label, value, position):
        """Helper function to add label and value in ID card"""
        page.insert_text(
            (position[0], position[1]),  # Position
            f"{label} {value}",  # Combine label and value
            fontsize=font_size, 
            fontname=font_bold if "MD Code" in label or "Registered On" in label else font_regular, 
            color=text_color
        )

     # Add user details to the PDF
    add_text("Name:", customer.name, text_positions["name"])
    add_text("Email:", customer.email, text_positions["email"])
    add_text("Mobile:", customer.mobile, text_positions["mobile"])
    add_text("DOB:", customer.dob.strftime('%d-%m-%Y') if customer.dob else "N/A", text_positions["dob"])  # ✅ Format DOB
    add_text("Posting State:", customer.posting_state or "N/A", text_positions["posting_state"])  # ✅ Posting State
    add_text("Posting District:", customer.posting_district or "N/A", text_positions["posting_district"])  # ✅ Posting District
    add_text("MD Code:", customer.md_code, text_positions["md_code"])
    add_text("Registered On:", customer.created_at.strftime('%d-%m-%Y'), text_positions["registered_on"])

    # Save the modified PDF
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename="Margdata_ID_Card.pdf")