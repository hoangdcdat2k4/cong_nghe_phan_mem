import streamlit as st
import pymongo
import pandas as pd
import datetime
import hashlib
import os
from bson.objectid import ObjectId
import re
from PIL import Image
import io
import base64

# MongoDB Atlas configuration
MONGODB_URI = "mongodb+srv://tunnguyen2910:Z8UUBbXK20o37JtO@cluster0.xvngw.mongodb.net/?retryWrites=true&w=majority"



def connect_to_mongodb():
    # Sử dụng biến môi trường MONGO_URI
    mongo_uri = os.environ.get("MONGO_URI")
    
    if not mongo_uri:
        st.error("MongoDB URI không tìm thấy. Vui lòng thiết lập biến môi trường MONGO_URI.")
        st.stop()
    
    client = pymongo.MongoClient(mongo_uri)
    db = client["hr_system"]
    return db

# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Validate email format
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

# Convert image to base64 for storage
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Convert base64 to image for display
def base64_to_image(base64_string):
    if base64_string:
        image_bytes = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(image_bytes))
    return None

# Initialize session state variables
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "page" not in st.session_state:
        st.session_state.page = "login"

# Authentication functions
def login(db, username, password):
    users_collection = db["users"]
    hashed_password = hash_password(password)
    user = users_collection.find_one({"username": username, "password": hashed_password})
    
    if user:
        st.session_state.logged_in = True
        st.session_state.user_id = str(user["_id"])
        st.session_state.username = username
        st.session_state.is_admin = user.get("is_admin", False)
        return True
    return False

def register(db, username, email, password, is_admin=False):
    users_collection = db["users"]
    
    # Check if username already exists
    if users_collection.find_one({"username": username}):
        return False, "Username already exists"
    
    # Check if email already exists
    if users_collection.find_one({"email": email}):
        return False, "Email already exists"
    
    # Validate email format
    if not is_valid_email(email):
        return False, "Invalid email format"
    
    # Create new user
    hashed_password = hash_password(password)
    user_data = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "is_admin": is_admin,
        "created_at": datetime.datetime.now()
    }
    
    users_collection.insert_one(user_data)
    return True, "Registration successful"

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.page = "login"

# Employee management functions
def add_employee(db, employee_data):
    # Chuyển đổi hire_date từ date sang datetime nếu cần
    if "hire_date" in employee_data and isinstance(employee_data["hire_date"], datetime.date):
        employee_data["hire_date"] = datetime.datetime.combine(
            employee_data["hire_date"], datetime.time.min
        )
    
    employees_collection = db["employees"]
    result = employees_collection.insert_one(employee_data)
    return result.inserted_id


def update_employee(db, employee_id, updated_data):
    employees_collection = db["employees"]
    result = employees_collection.update_one(
        {"_id": ObjectId(employee_id)},
        {"$set": updated_data}
    )
    return result.modified_count > 0

def delete_employee(db, employee_id):
    employees_collection = db["employees"]
    result = employees_collection.delete_one({"_id": ObjectId(employee_id)})
    return result.deleted_count > 0

def get_employee(db, employee_id):
    employees_collection = db["employees"]
    return employees_collection.find_one({"_id": ObjectId(employee_id)})

def get_all_employees(db):
    employees_collection = db["employees"]
    return list(employees_collection.find())

def get_employee_by_user_id(db, user_id):
    employees_collection = db["employees"]
    return employees_collection.find_one({"user_id": user_id})

# Department management functions
def add_department(db, department_data):
    departments_collection = db["departments"]
    result = departments_collection.insert_one(department_data)
    return result.inserted_id

def update_department(db, department_id, updated_data):
    departments_collection = db["departments"]
    result = departments_collection.update_one(
        {"_id": ObjectId(department_id)},
        {"$set": updated_data}
    )
    return result.modified_count > 0

def delete_department(db, department_id):
    departments_collection = db["departments"]
    result = departments_collection.delete_one({"_id": ObjectId(department_id)})
    return result.deleted_count > 0

def get_all_departments(db):
    departments_collection = db["departments"]
    return list(departments_collection.find())

# Employment history functions
def add_employment_history(db, history_data):
    history_collection = db["employment_history"]
    result = history_collection.insert_one(history_data)
    return result.inserted_id

def get_employee_history(db, employee_id):
    history_collection = db["employment_history"]
    return list(history_collection.find({"employee_id": employee_id}).sort("date", -1))

# UI Components
def render_login_page(db):
    st.markdown("""
        <h1 style="text-align: center; color: #1E3A8A; margin-bottom: 2rem;">
            HR Information System
            <span style="display: block; font-size: 1.2rem; color: #64748B; margin-top: 0.5rem;">
                Manage your workforce efficiently
            </span>
        </h1>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login(db, username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with col2:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        if st.button("Register"):
            if reg_password != reg_confirm_password:
                st.error("Passwords do not match")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success, message = register(db, reg_username, reg_email, reg_password)
                if success:
                    st.success(message)
                    st.info("Please login with your new account")
                else:
                    st.error(message)

def render_admin_dashboard(db):
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: #1E3A8A;">HR System - Admin Dashboard</h1>
            <p style="color: #64748B;">Manage your organization's human resources</p>
        </div>
    """, unsafe_allow_html=True)
    
    employees = get_all_employees(db)
    departments = get_all_departments(db)
    total_employees = len(employees)
    active_employees = sum(1 for emp in employees if emp.get('status', '') == 'Active')
    on_leave = sum(1 for emp in employees if emp.get('status', '') == 'On Leave')
    total_departments = len(departments)
    
    # Create metric cards in a row with styled cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="dashboard-card" style="text-align: center; background: linear-gradient(135deg, #1E88E5, #1565C0); padding: 15px; border-radius: 10px;">
                <img src="https://cdn-icons-png.flaticon.com/512/3126/3126647.png" width="50px" style="margin-bottom: 10px;">
                <h2 style="color: white; font-size: 2rem; margin: 0;">{total_employees}</h2>
                <p style="color: white; opacity: 0.8; margin: 0;">Total Employees</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="dashboard-card" style="text-align: center; background: linear-gradient(135deg, #4CAF50, #2E7D32); padding: 15px; border-radius: 10px;">
                <img src="https://cdn-icons-png.flaticon.com/512/1828/1828640.png" width="50px" style="margin-bottom: 10px;">
                <h2 style="color: white; font-size: 2rem; margin: 0;">{active_employees}</h2>
                <p style="color: white; opacity: 0.8; margin: 0;">Active Employees</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="dashboard-card" style="text-align: center; background: linear-gradient(135deg, #FF9800, #EF6C00); padding: 15px; border-radius: 10px;">
                <img src="https://cdn-icons-png.flaticon.com/512/1063/1063237.png" width="50px" style="margin-bottom: 10px;">
                <h2 style="color: white; font-size: 2rem; margin: 0;">{total_departments}</h2>
                <p style="color: white; opacity: 0.8; margin: 0;">Departments</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="dashboard-card" style="text-align: center; background: linear-gradient(135deg, #9C27B0, #6A1B9A); padding: 15px; border-radius: 10px;">
                <img src="https://cdn-icons-png.flaticon.com/512/2921/2921222.png" width="50px" style="margin-bottom: 10px;">
                <h2 style="color: white; font-size: 2rem; margin: 0;">{on_leave}</h2>
                <p style="color: white; opacity: 0.8; margin: 0;">On Leave</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Create navigation menu with icons
    st.markdown("<h3 style='text-align: center; margin-top: 2rem;'>Choose a module:</h3>", unsafe_allow_html=True)
    
    # Use columns for the menu items
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 15px;">
                <img src="https://cdn-icons-png.flaticon.com/512/2321/2321089.png" width="40">
            </div>
        """, unsafe_allow_html=True)
        emp_management = st.button("Employee Management", use_container_width=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 15px;">
                <img src="https://cdn-icons-png.flaticon.com/512/3281/3281346.png" width="40">
            </div>
        """, unsafe_allow_html=True)
        dept_management = st.button("Department Management", use_container_width=True)
    
    with col3:
        st.markdown("""
            <div style="text-align: center; padding: 15px;">
                <img src="https://cdn-icons-png.flaticon.com/512/1055/1055644.png" width="40">
            </div>
        """, unsafe_allow_html=True)
        reports = st.button("Reports", use_container_width=True)
    
    # Handle navigation based on button clicks
    if emp_management:
        st.session_state.admin_page = "employee_management"
        st.rerun()
    elif dept_management:
        st.session_state.admin_page = "department_management"
        st.rerun()
    elif reports:
        st.session_state.admin_page = "reports"
        st.rerun()
    
    # Display the appropriate page based on session state
    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "employee_management"
    
    if st.session_state.admin_page == "employee_management":
        render_employee_management(db)
    elif st.session_state.admin_page == "department_management":
        render_department_management(db)
    elif st.session_state.admin_page == "reports":
        render_reports(db)
    
    # Add logout button to sidebar
    with st.sidebar:
        st.title("Admin Panel")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()


def render_employee_management(db):
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
            <img src="https://cdn-icons-png.flaticon.com/512/1256/1256650.png" width="40px" style="margin-right: 15px;">
            <h2 style="margin: 0; color: #1E3A8A;">Employee Management</h2>
        </div>
    """, unsafe_allow_html=True)
    
    
    tab1, tab2, tab3 = st.tabs(["Employee List", "Add Employee", "Employment History"])
    
    with tab1:
        employees = get_all_employees(db)
        if employees:
            st.markdown('<div class="glass-effect" style="padding: 1rem; margin-bottom: 1.5rem;">', unsafe_allow_html=True)
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_term = st.text_input("🔍 Search employees by name, email, or department", placeholder="Type to search...")
            with search_col2:
                status_filter = st.selectbox("Filter by Status", ["All", "Active", "On Leave", "Terminated"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            filtered_employees = employees
            if search_term:
                filtered_employees = [
                    emp for emp in employees if 
                    search_term.lower() in f"{emp.get('first_name', '')} {emp.get('last_name', '')}".lower() or
                    search_term.lower() in emp.get('email', '').lower() or
                    search_term.lower() in emp.get('department', '').lower()
                ]
            
            if status_filter != "All":
                filtered_employees = [emp for emp in filtered_employees if emp.get('status', '') == status_filter]
            
            # Convert MongoDB documents to a more display-friendly format
            display_data = []
            for emp in employees:
                display_data.append({
                    "ID": str(emp["_id"]),
                    "Name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                    "Email": emp.get("email", ""),
                    "Department": emp.get("department", ""),
                    "Position": emp.get("position", ""),
                    "Status": emp.get("status", "Active")
                })
            
            df = pd.DataFrame(display_data)
            st.dataframe(df)
            
            # Employee details and actions
            selected_emp_id = st.selectbox("Select Employee for Details/Actions", 
                                          [emp["ID"] for emp in display_data])
            
            if selected_emp_id:
                employee = get_employee(db, selected_emp_id)
                if employee:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Employee Details")
                        st.markdown('<div class="employee-card">', unsafe_allow_html=True)
                        st.write(f"**Name:** {employee.get('first_name', '')} {employee.get('last_name', '')}")
                        st.write(f"**Email:** {employee.get('email', '')}")
                        st.write(f"**Phone:** {employee.get('phone', '')}")
                        st.write(f"**Department:** {employee.get('department', '')}")
                        st.write(f"**Position:** {employee.get('position', '')}")
                        st.write(f"**Hire Date:** {employee.get('hire_date', '')}")
                        st.write(f"**Status:** {employee.get('status', 'Active')}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display profile picture if available
                        if "profile_picture" in employee:
                            try:
                                img = base64_to_image(employee["profile_picture"])
                                if img:
                                    st.image(img, width=150, caption="Profile Picture")
                            except Exception as e:
                                st.error(f"Error displaying image: {e}")
                    
                    with col2:
                        st.subheader("Actions")
                        action = st.radio("Choose Action", ["Edit", "Delete", "View History"])
                        
                        if action == "Edit":
                            st.subheader("Edit Employee")
                            updated_first_name = st.text_input("First Name", employee.get("first_name", ""))
                            updated_last_name = st.text_input("Last Name", employee.get("last_name", ""))
                            updated_email = st.text_input("Email", employee.get("email", ""))
                            updated_phone = st.text_input("Phone", employee.get("phone", ""))
                            
                            departments = [dept["name"] for dept in get_all_departments(db)]
                            updated_department = st.selectbox("Department", departments, 
                                                            index=departments.index(employee.get("department", "")) if employee.get("department", "") in departments else 0,
                                                            key=f"edit_department_{selected_emp_id}")
                            updated_position = st.text_input("Position", employee.get("position", ""), 
                                                            key=f"edit_position_{selected_emp_id}")
                            updated_status = st.selectbox("Status", ["Active", "On Leave", "Terminated"], 
                                                        index=["Active", "On Leave", "Terminated"].index(employee.get("status", "Active")),
                                                        key=f"edit_status_{selected_emp_id}")                            
                            if st.button("Update Employee"):
                                updated_data = {
                                    "first_name": updated_first_name,
                                    "last_name": updated_last_name,
                                    "email": updated_email,
                                    "phone": updated_phone,
                                    "department": updated_department,
                                    "position": updated_position,
                                    "status": updated_status,
                                    "updated_at": datetime.datetime.now()
                                }
                                
                                if update_employee(db, selected_emp_id, updated_data):
                                    st.success("Employee updated successfully")
                                    
                                    # Add to employment history if position or department changed
                                    if (updated_department != employee.get("department", "") or 
                                        updated_position != employee.get("position", "") or
                                        updated_status != employee.get("status", "Active")):
                                        
                                        history_data = {
                                            "employee_id": selected_emp_id,
                                            "date": datetime.datetime.now(),
                                            "type": "Update",
                                            "old_department": employee.get("department", ""),
                                            "new_department": updated_department,
                                            "old_position": employee.get("position", ""),
                                            "new_position": updated_position,
                                            "old_status": employee.get("status", "Active"),
                                            "new_status": updated_status,
                                            "notes": "Employee information updated by admin"
                                        }
                                        add_employment_history(db, history_data)
                                    
                                    st.rerun()
                                else:
                                    st.error("Failed to update employee")
                        
                        elif action == "Delete":
                            st.warning("Are you sure you want to delete this employee? This action cannot be undone.")
                            if st.button("Confirm Delete"):
                                if delete_employee(db, selected_emp_id):
                                    st.success("Employee deleted successfully")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete employee")
                        
                        elif action == "View History":
                            st.subheader("Employment History")
                            history = get_employee_history(db, selected_emp_id)
                            
                            if history:
                                for entry in history:
                                    with st.expander(f"{entry['type']} - {entry['date'].strftime('%Y-%m-%d %H:%M')}"):
                                        if entry['type'] == "Update":
                                            if entry['old_department'] != entry['new_department']:
                                                st.write(f"Department changed from **{entry['old_department']}** to **{entry['new_department']}**")
                                            if entry['old_position'] != entry['new_position']:
                                                st.write(f"Position changed from **{entry['old_position']}** to **{entry['new_position']}**")
                                            if entry['old_status'] != entry['new_status']:
                                                st.write(f"Status changed from **{entry['old_status']}** to **{entry['new_status']}**")
                                                st.write(f"Notes: {entry.get('notes', 'No notes')}")
                            else:
                                st.info("No employment history found for this employee")
        else:
            st.info("No employees found. Add some employees to get started.")
    
    with tab2:
        st.subheader("Add New Employee")
        
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", key="add_first_name")
            last_name = st.text_input("Last Name", key="add_last_name")
            email = st.text_input("Email", key="add_email")
            phone = st.text_input("Phone", key="add_phone")
        
        with col2:
            departments = [dept["name"] for dept in get_all_departments(db)]
            department = st.selectbox("Department", departments if departments else [""], key="add_employee_department")
            position = st.text_input("Position", key="add_employee_position")
            hire_date = st.date_input("Hire Date", datetime.datetime.now(), key="add_employee_hire_date")
            hire_date_datetime = datetime.datetime.combine(hire_date, datetime.time.min)
            status = st.selectbox("Status", ["Active", "On Leave", "Terminated"], key="add_employee_status")
        
        # Optional: Create user account for employee
        create_account = st.checkbox("Create User Account for Employee")
        if create_account:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
        
        # Profile picture upload
        uploaded_file = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"])
        profile_picture_base64 = None
        if uploaded_file is not None:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", width=150)
                profile_picture_base64 = image_to_base64(image)
            except Exception as e:
                st.error(f"Error processing image: {e}")
        
        if st.button("Add Employee"):
            if not first_name or not last_name or not email:
                st.error("First name, last name, and email are required")
            elif not is_valid_email(email):
                st.error("Invalid email format")
            else:
                # Create user account if requested
                user_id = None
                if create_account:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                        st.stop()
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                        st.stop()
                    else:
                        success, message = register(db, username, email, password)
                        if success:
                            st.success("User account created successfully")
                            # Get the user_id of the newly created user
                            users_collection = db["users"]
                            user = users_collection.find_one({"username": username})
                            if user:
                                user_id = str(user["_id"])
                        else:
                            st.error(f"Failed to create user account: {message}")
                            st.stop()
                
                # Create employee record
                employee_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "department": department,
                    "position": position,
                    "hire_date": hire_date_datetime,
                    "status": status,
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }
                
                if user_id:
                    employee_data["user_id"] = user_id
                
                if profile_picture_base64:
                    try:
                        # Kiểm tra kích thước trước khi thêm vào document
                        if len(profile_picture_base64) > 15 * 1024 * 1024:  # 15MB limit
                            st.warning("Profile picture quá lớn. Vui lòng tải lên ảnh nhỏ hơn.")
                        else:
                            employee_data["profile_picture"] = profile_picture_base64
                    except Exception as e:
                        st.error(f"Lỗi xử lý ảnh: {e}")
                
                employee_id = add_employee(db, employee_data)
                
                if employee_id:
                    st.success("Employee added successfully")
                    
                    # Add to employment history
                    history_data = {
                        "employee_id": str(employee_id),
                        "date": datetime.datetime.now(),
                        "type": "Hire",
                        "old_department": "",
                        "new_department": department,
                        "old_position": "",
                        "new_position": position,
                        "old_status": "",
                        "new_status": status,
                        "notes": f"Employee hired on {hire_date}"
                    }
                    add_employment_history(db, history_data)
                    
                    st.rerun()
                else:
                    st.error("Failed to add employee")
    
    with tab3:
        st.subheader("Employment History Overview")
        
        employees = get_all_employees(db)
        if employees:
            employee_options = [f"{emp.get('first_name', '')} {emp.get('last_name', '')} ({emp.get('email', '')})" for emp in employees]
            employee_map = {f"{emp.get('first_name', '')} {emp.get('last_name', '')} ({emp.get('email', '')})": str(emp["_id"]) for emp in employees}
            
            selected_employee = st.selectbox("Select Employee", employee_options, key="history_employee_select")
            if selected_employee:
                employee_id = employee_map[selected_employee]
                history = get_employee_history(db, employee_id)
                
                if history:
                    history_data = []
                    for entry in history:
                        history_data.append({
                            "Date": entry["date"].strftime("%Y-%m-%d %H:%M"),
                            "Type": entry["type"],
                            "Old Department": entry.get("old_department", ""),
                            "New Department": entry.get("new_department", ""),
                            "Old Position": entry.get("old_position", ""),
                            "New Position": entry.get("new_position", ""),
                            "Old Status": entry.get("old_status", ""),
                            "New Status": entry.get("new_status", ""),
                            "Notes": entry.get("notes", "")
                        })
                    
                    df = pd.DataFrame(history_data)
                    st.dataframe(df)
                    
                    # Add new history entry manually
                    with st.expander("Add New History Entry"):
                        entry_type = st.selectbox("Entry Type", ["Promotion", "Transfer", "Status Change", "Other"], 
                         key="history_entry_type")
                        entry_date = st.date_input("Date", datetime.datetime.now())
                        
                        employee = get_employee(db, employee_id)
                        current_department = employee.get("department", "")
                        current_position = employee.get("position", "")
                        current_status = employee.get("status", "Active")
                        
                        new_department = st.text_input("New Department", current_department)
                        new_position = st.text_input("New Position", current_position)
                        new_status = st.selectbox("New Status", ["Active", "On Leave", "Terminated"], 
                        index=["Active", "On Leave", "Terminated"].index(current_status),
                        key="history_new_status")


                        notes = st.text_area("Notes")
                        
                        if st.button("Add History Entry"):
                            history_data = {
                                "employee_id": employee_id,
                                "date": entry_date,
                                "type": entry_type,
                                "old_department": current_department,
                                "new_department": new_department,
                                "old_position": current_position,
                                "new_position": new_position,
                                "old_status": current_status,
                                "new_status": new_status,
                                "notes": notes
                            }
                            
                            add_employment_history(db, history_data)
                            
                            # Update employee record if needed
                            if (new_department != current_department or 
                                new_position != current_position or 
                                new_status != current_status):
                                
                                updated_data = {
                                    "department": new_department,
                                    "position": new_position,
                                    "status": new_status,
                                    "updated_at": datetime.datetime.now()
                                }
                                
                                update_employee(db, employee_id, updated_data)
                            
                            st.success("History entry added successfully")
                            st.rerun()
                else:
                    st.info("No employment history found for this employee")
        else:
            st.info("No employees found. Add some employees to view history.")

def render_department_management(db):
    st.header("Department Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add New Department")
        dept_name = st.text_input("Department Name")
        dept_description = st.text_area("Description")
        dept_manager = st.text_input("Department Manager")
        
        if st.button("Add Department"):
            if not dept_name:
                st.error("Department name is required")
            else:
                department_data = {
                    "name": dept_name,
                    "description": dept_description,
                    "manager": dept_manager,
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }
                
                if add_department(db, department_data):
                    st.success("Department added successfully")
                    st.rerun()
                else:
                    st.error("Failed to add department")
    
    with col2:
        st.subheader("Department List")
        departments = get_all_departments(db)
        
        if departments:
            for dept in departments:
                with st.expander(dept["name"]):
                    st.markdown('<div class="department-card">', unsafe_allow_html=True)
                    st.write(f"**Description:** {dept.get('description', 'No description')}")
                    st.write(f"**Manager:** {dept.get('manager', 'No manager assigned')}")
                    
                    # Count employees in this department
                    employees_collection = db["employees"]
                    employee_count = employees_collection.count_documents({"department": dept["name"]})
                    st.write(f"**Number of Employees:** {employee_count}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit", key=f"edit_{dept['_id']}"):
                            st.session_state.edit_dept_id = str(dept["_id"])
                    with col2:
                        if st.button("Delete", key=f"delete_{dept['_id']}"):
                            if delete_department(db, str(dept["_id"])):
                                st.success("Department deleted successfully")
                                st.rerun()
                            else:
                                st.error("Failed to delete department")
            
            # Edit department form
            if hasattr(st.session_state, "edit_dept_id"):
                dept_id = st.session_state.edit_dept_id
                departments_collection = db["departments"]
                dept = departments_collection.find_one({"_id": ObjectId(dept_id)})
                
                if dept:
                    st.subheader(f"Edit Department: {dept['name']}")
                    updated_name = st.text_input("Department Name", dept["name"])
                    updated_description = st.text_area("Description", dept.get("description", ""))
                    updated_manager = st.text_input("Department Manager", dept.get("manager", ""))
                    
                    if st.button("Update Department"):
                        updated_data = {
                            "name": updated_name,
                            "description": updated_description,
                            "manager": updated_manager,
                            "updated_at": datetime.datetime.now()
                        }
                        
                        if update_department(db, dept_id, updated_data):
                            # If department name changed, update all employees in this department
                            if updated_name != dept["name"]:
                                employees_collection = db["employees"]
                                employees_collection.update_many(
                                    {"department": dept["name"]},
                                    {"$set": {"department": updated_name}}
                                )
                            
                            st.success("Department updated successfully")
                            del st.session_state.edit_dept_id
                            st.rerun()
                        else:
                            st.error("Failed to update department")
        else:
            st.info("No departments found. Add some departments to get started.")

def render_reports(db):
    st.header("HR Reports")
    
    report_type = st.selectbox("Select Report Type", [
    "Employee Distribution by Department",
    "Employee Status Overview",
    "Recent Employment Changes",
    "Department Structure"
], key="report_type_select")


    
    if report_type == "Employee Distribution by Department":
        st.subheader("Employee Distribution by Department")
        
        # Get all employees
        employees = get_all_employees(db)
        
        if employees:
            # Count employees by department
            dept_counts = {}
            for emp in employees:
                dept = emp.get("department", "No Department")
                if dept in dept_counts:
                    dept_counts[dept] += 1
                else:
                    dept_counts[dept] = 1
            
            # Create dataframe for chart
            df = pd.DataFrame({
                "Department": list(dept_counts.keys()),
                "Number of Employees": list(dept_counts.values())
            })
            
            # Display as chart and table
            st.bar_chart(df.set_index("Department"))
            st.dataframe(df)
        else:
            st.info("No employee data available for reporting")
    
    elif report_type == "Employee Status Overview":
        st.subheader("Employee Status Overview")
        
        # Get all employees
        employees = get_all_employees(db)
        
        if employees:
            # Count employees by status
            status_counts = {}
            for emp in employees:
                status = emp.get("status", "Unknown")
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
            
            # Create dataframe for chart
            df = pd.DataFrame({
                "Status": list(status_counts.keys()),
                "Number of Employees": list(status_counts.values())
            })
            
            # Display as chart and table
            st.bar_chart(df.set_index("Status"))
            st.dataframe(df)
            
            # Calculate percentages
            total = sum(status_counts.values())
            st.write(f"Total Employees: {total}")
            for status, count in status_counts.items():
                percentage = (count / total) * 100
                st.write(f"{status}: {count} ({percentage:.1f}%)")
        else:
            st.info("No employee data available for reporting")
    
    elif report_type == "Recent Employment Changes":
        st.subheader("Recent Employment Changes")
        
        # Get recent history entries
        history_collection = db["employment_history"]
        recent_changes = list(history_collection.find().sort("date", -1).limit(20))
        
        if recent_changes:
            # Process data for display
            change_data = []
            for change in recent_changes:
                # Get employee name
                employee = get_employee(db, change["employee_id"])
                employee_name = "Unknown"
                if employee:
                    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
                change_data.append({
                    "Date": change["date"].strftime("%Y-%m-%d"),
                    "Employee": employee_name,
                    "Type": change["type"],
                    "Details": get_change_details(change),
                    "Notes": change.get("notes", "")
                })
            
            # Display as table
            df = pd.DataFrame(change_data)
            st.dataframe(df)
        else:
            st.info("No recent employment changes found")
    
    elif report_type == "Department Structure":
        st.subheader("Department Structure")
        
        # Get all departments
        departments = get_all_departments(db)
        
        if departments:
            # For each department, show structure
            for dept in departments:
                with st.expander(f"{dept['name']} - Manager: {dept.get('manager', 'None')}"):
                    # Get employees in this department
                    employees_collection = db["employees"]
                    dept_employees = list(employees_collection.find({"department": dept["name"]}))
                    
                    if dept_employees:
                        # Group by position
                        positions = {}
                        for emp in dept_employees:
                            position = emp.get("position", "No Position")
                            if position not in positions:
                                positions[position] = []
                            positions[position].append(f"{emp.get('first_name', '')} {emp.get('last_name', '')}")
                        
                        # Display by position
                        for position, employees in positions.items():
                            st.write(f"**{position}**")
                            for employee in employees:
                                st.write(f"- {employee}")
                    else:
                        st.write("No employees in this department")
        else:
            st.info("No departments found")

def get_change_details(change):
    """Extract meaningful details from a change record"""
    details = []
    
    if change["type"] == "Hire":
        return f"Hired as {change['new_position']} in {change['new_department']}"
    
    if change["type"] == "Update" or change["type"] == "Promotion" or change["type"] == "Transfer":
        if change["old_department"] != change["new_department"]:
            details.append(f"Department: {change['old_department']} → {change['new_department']}")
        if change["old_position"] != change["new_position"]:
            details.append(f"Position: {change['old_position']} → {change['new_position']}")
        if change["old_status"] != change["new_status"]:
            details.append(f"Status: {change['old_status']} → {change['new_status']}")
    
    return ", ".join(details) if details else "No significant changes"

def render_user_dashboard(db):
    st.title(f"HR System - Employee Portal")
    st.write(f"Welcome, {st.session_state.username}!")
    
    # Get employee information
    employee = get_employee_by_user_id(db, st.session_state.user_id)
    
    if employee:
        menu = ["My Profile", "Update Information", "Employment History"]
        choice = st.sidebar.selectbox("Menu", menu)
        
        if choice == "My Profile":
            render_employee_profile(db, employee)
        elif choice == "Update Information":
            render_update_employee_info(db, employee)
        elif choice == "Employment History":
            render_employee_history_view(db, employee)
    else:
        st.warning("Your employee profile is not set up. Please contact HR.")
    
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

def render_employee_profile(db, employee):
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.header("My Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Display profile picture if available
        if "profile_picture" in employee:
            try:
                img = base64_to_image(employee["profile_picture"])
                if img:
                    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
                    st.image(img, width=200)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown(f'<h3 style="text-align: center;">{employee.get("first_name", "")} {employee.get("last_name", "")}</h3>', unsafe_allow_html=True)
                   
            except Exception as e:
                st.error(f"Error displaying image: {e}")
        else:
            st.markdown("""
                <div class="profile-container" style="width: 200px; height: 200px; display: flex; align-items: center; justify-content: center;">
                    <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="150px">
                </div>
                <h3 style="text-align: center;">""" + f"{employee.get('first_name', '')} {employee.get('last_name', '')}" + """</h3>
            """, unsafe_allow_html=True)
           
        st.markdown('<div class="glass-effect" style="padding: 1rem; margin-top: 1rem;">', unsafe_allow_html=True)
        st.subheader("Personal Information")
        st.write(f"**Name:** {employee.get('first_name', '')} {employee.get('last_name', '')}")
        st.write(f"**Email:** {employee.get('email', '')}")
        st.write(f"**Phone:** {employee.get('phone', '')}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-effect" style="padding: 1rem;">', unsafe_allow_html=True)
        st.subheader("Employment Information")
        st.write(f"**Department:** {employee.get('department', '')}")
        st.write(f"**Position:** {employee.get('position', '')}")
        st.write(f"**Status:** {employee.get('status', '')}")
        st.write(f"**Hire Date:** {employee.get('hire_date', '')}")
        # Department with icon
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <img src="https://cdn-icons-png.flaticon.com/512/1063/1063237.png" width="20px" style="margin-right: 10px;">
                <span><strong>Department:</strong> {employee.get('department', '')}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Position with icon
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <img src="https://cdn-icons-png.flaticon.com/512/1534/1534938.png" width="20px" style="margin-right: 10px;">
                <span><strong>Position:</strong> {employee.get('position', '')}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Status with colored indicator
        status = employee.get('status', '')
        status_class = "status-active"
        if status == "On Leave":
            status_class = "status-leave"
        elif status == "Terminated":
            status_class = "status-terminated"
            
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <img src="https://cdn-icons-png.flaticon.com/512/1828/1828640.png" width="20px" style="margin-right: 10px;">
                <span><strong>Status:</strong> <span class="{status_class}">{status}</span></span>
            </div>
        """, unsafe_allow_html=True)
        
        # Hire date with icon
        hire_date = employee.get('hire_date', '')
        hire_date_str = hire_date.strftime("%Y-%m-%d") if isinstance(hire_date, datetime.datetime) else str(hire_date)
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <img src="https://cdn-icons-png.flaticon.com/512/2693/2693507.png" width="20px" style="margin-right: 10px;">
                <span><strong>Hire Date:</strong> {hire_date_str}</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        
        # Get manager information
        departments_collection = db["departments"]
        department = departments_collection.find_one({"name": employee.get('department', '')})
        if department and "manager" in department:
            st.write(f"**Department Manager:** {department['manager']}")

def render_update_employee_info(db, employee):
    st.markdown('<div class="glass-effect" style="padding: 1rem; margin-top: 1rem;">', unsafe_allow_html=True)
    st.header("Update My Information")
    st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2321/2321232.png" width="20px" style="margin-right: 10px;">
                    <span><strong>Manager:</strong> {department['manager']}</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <img src="https://cdn-icons-png.flaticon.com/512/1484/1484799.png" width="20px" style="margin-right: 10px;">
                    <span><strong>Description:</strong> {department.get('description', 'No description available')}</span>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("You can update your personal information here. For changes to employment information, please contact HR.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        updated_first_name = st.text_input("First Name", employee.get("first_name", ""))
        updated_last_name = st.text_input("Last Name", employee.get("last_name", ""))
        updated_email = st.text_input("Email", employee.get("email", ""))
        updated_phone = st.text_input("Phone", employee.get("phone", ""))
    
    with col2:
        # Profile picture upload
        st.write("Update Profile Picture")
        
        # Display current profile picture if available
        if "profile_picture" in employee:
            try:
                img = base64_to_image(employee["profile_picture"])
                if img:
                    st.image(img, width=150, caption="Current Profile Picture")
            except Exception as e:
                st.error(f"Error displaying image: {e}")
        
        uploaded_file = st.file_uploader("Upload New Profile Picture", type=["jpg", "jpeg", "png"])
        profile_picture_base64 = None
        if uploaded_file is not None:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="New Profile Picture", width=150)
                profile_picture_base64 = image_to_base64(image)
            except Exception as e:
                st.error(f"Error processing image: {e}")
    
    if st.button("Update Information"):
        updated_data = {
            "first_name": updated_first_name,
            "last_name": updated_last_name,
            "email": updated_email,
            "phone": updated_phone,
            "updated_at": datetime.datetime.now()
        }
        
        if profile_picture_base64:
            updated_data["profile_picture"] = profile_picture_base64
        
        if update_employee(db, str(employee["_id"]), updated_data):
            st.success("Information updated successfully")
            st.rerun()
        else:
            st.error("Failed to update information")

def render_employee_history_view(db, employee):
    st.header("My Employment History")
    
    history = get_employee_history(db, str(employee["_id"]))
    
    if history:
        for entry in history:
            with st.expander(f"{entry['type']} - {entry['date'].strftime('%Y-%m-%d')}"):
                if entry['type'] == "Hire":
                    st.write(f"You were hired as **{entry['new_position']}** in **{entry['new_department']}**")
                elif entry['type'] == "Update" or entry['type'] == "Promotion" or entry['type'] == "Transfer":
                    if entry['old_department'] != entry['new_department']:
                        st.write(f"Department changed from **{entry['old_department']}** to **{entry['new_department']}**")
                    if entry['old_position'] != entry['new_position']:
                        st.write(f"Position changed from **{entry['old_position']}** to **{entry['new_position']}**")
                    if entry['old_status'] != entry['new_status']:
                        st.write(f"Status changed from **{entry['old_status']}** to **{entry['new_status']}**")
                st.write(f"Notes: {entry.get('notes', 'No notes')}")
    else:
        st.info("No employment history found")


def set_custom_style():
    st.markdown("""
    <style>
        /* Main styling */
        .main .block-container {
            padding: 2rem;
            max-width: 1200px;
        }
        
        /* Card styling */
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        div[data-testid="stMetric"] > div {
            display: flex;
            justify-content: center;
        }
        
        div[data-testid="stMetric"] label {
            font-size: 1rem !important;
            color: #64748B !important;
        }
        
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: bold !important;
            color: #1E3A8A !important;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #1E3A8A;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton button:hover {
            background-color: #2563EB;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        /* Image centering */
        .stImage {
            text-align: center;
            margin: 0 auto;
            display: block;
        }
    </style>
    """, unsafe_allow_html=True)

# Main application



def main():
    st.set_page_config(
        page_title="HR Information System",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    set_custom_style()
    st.markdown("""
    <style>
        /* Main styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styling */
        h1, h2, h3 {
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        
        /* Card-like styling for sections */
        .stExpander {
            border: 1px solid #E5E7EB;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        /* Button styling */
        .stButton button {
            border-radius: 0.25rem;
            background-color: #1E88E5;
            color: white;
            font-weight: 500;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
        }
        
        .stButton button:hover {
            background-color: #1565C0;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        /* Delete button styling */
        button[key*="delete"] {
            background-color: #F44336 !important;
        }
        
        button[key*="delete"]:hover {
            background-color: #D32F2F !important;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #F8F9FA;
        }
        
        /* Dataframe styling */
        .stDataFrame {
            border-radius: 0.5rem;
            overflow: hidden;
            border: 1px solid #E5E7EB;
        }
        
        /* Form input styling */
        input, textarea, select {
            border-radius: 0.25rem !important;
            border: 1px solid #E5E7EB !important;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            border-radius: 0.5rem 0.5rem 0 0;
            padding: 0 1rem;
        }
        
        /* Success/Error message styling */
        .stAlert {
            border-radius: 0.25rem;
            padding: 0.75rem 1rem;
        }
        
        /* Profile picture container */
        .profile-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1rem;
            background-color: #F8F9FA;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        /* Employee card styling */
        .employee-card {
            padding: 1rem;
            border: 1px solid #E5E7EB;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        /* Department card styling */
        .department-card {
            padding: 1rem;
            border-left: 4px solid #1E88E5;
            background-color: #F8F9FA;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    
    # Initialize session state
    init_session_state()
    
    # Connect to MongoDB
    db = connect_to_mongodb()
    
    # Check if admin exists, create one if not
    users_collection = db["users"]
    admin_exists = users_collection.find_one({"is_admin": True})
    if not admin_exists:
        # Create default admin user
        register(db, "admin", "admin@example.com", "admin123", is_admin=True)
        st.sidebar.success("Default admin account created: admin / admin123")
    
    # Display appropriate page based on login status
    if not st.session_state.logged_in:
        render_login_page(db)
    else:
        if st.session_state.is_admin:
            render_admin_dashboard(db)
        else:
            render_user_dashboard(db)

if __name__ == "__main__":
    main()
        
