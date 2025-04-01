import os
import streamlit as st
import pandas as pd
import django
from django.conf import settings
from django.core.files.base import ContentFile
import tempfile
import io

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment_project.settings')

# Only attempt to configure Django if it hasn't been configured yet
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'djongo',
                'NAME': 'recruitment_db',
                'CLIENT': {
                    'host': 'mongodb://localhost:27017',  # Update with your MongoDB connection string
                }
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'recruitment_app',
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        MEDIA_ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media'),
        MEDIA_URL='/media/',
    )
    django.setup()

# Now import Django models after Django is configured
from django.shortcuts import get_object_or_404
from djongo import models

# Define models
class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    company = models.CharField(max_length=255)
    posted_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Applicant(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    cv = models.FileField(upload_to='cv/')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('interview', 'Interview'), ('hired', 'Hired')])
    
    def __str__(self):
        return self.name

# Streamlit functions
def job_list():
    try:
        jobs = Job.objects.all()
        if jobs.exists():
            job_data = pd.DataFrame(list(jobs.values()))
            st.title("Danh sách công việc")
            st.dataframe(job_data)
        else:
            st.title("Danh sách công việc")
            st.info("Không có công việc nào trong hệ thống.")
    except Exception as e:
        st.error(f"Lỗi khi tải danh sách công việc: {str(e)}")

def apply_job():
    st.title("Ứng tuyển công việc")
    
    try:
        jobs = Job.objects.all()
        if not jobs.exists():
            st.info("Không có công việc nào để ứng tuyển.")
            return
            
        job_options = {job.id: job.title for job in jobs}
        job_id = st.selectbox("Chọn công việc", options=list(job_options.keys()), format_func=lambda x: job_options[x])
        
        name = st.text_input("Tên")
        email = st.text_input("Email")
        cv_file = st.file_uploader("Tải lên CV", type=["pdf", "docx"])
        
        if st.button("Nộp đơn"):
            if not name or not email or not cv_file:
                st.warning("Vui lòng điền đầy đủ thông tin và tải lên CV.")
                return
                
            job = get_object_or_404(Job, id=job_id)
            
            # Handle file upload
            file_content = cv_file.read()
            file_name = cv_file.name
            
            # Create a new applicant
            applicant = Applicant(name=name, email=email, job=job, status='pending')
            
            # Save the applicant to get an ID
            applicant.save()
            
            # Now handle the file
            applicant.cv.save(file_name, ContentFile(file_content))
            applicant.save()
            
            st.success("Ứng tuyển thành công!")
    except Exception as e:
        st.error(f"Lỗi khi ứng tuyển: {str(e)}")

def add_job():
    st.title("Thêm công việc mới")
    
    title = st.text_input("Tiêu đề công việc")
    company = st.text_input("Tên công ty")
    description = st.text_area("Mô tả công việc")
    
    if st.button("Thêm công việc"):
        if not title or not company or not description:
            st.warning("Vui lòng điền đầy đủ thông tin công việc.")
            return
            
        try:
            Job.objects.create(
                title=title,
                company=company,
                description=description
            )
            st.success("Thêm công việc thành công!")
        except Exception as e:
            st.error(f"Lỗi khi thêm công việc: {str(e)}")

def view_applicants():
    st.title("Danh sách ứng viên")
    
    try:
        applicants = Applicant.objects.all().select_related('job')
        if not applicants.exists():
            st.info("Chưa có ứng viên nào.")
            return
            
        applicant_data = []
        for app in applicants:
            applicant_data.append({
                'ID': app.id,
                'Tên': app.name,
                'Email': app.email,
                'Công việc': app.job.title,
                'Trạng thái': app.status
            })
        
        df = pd.DataFrame(applicant_data)
        st.dataframe(df)
        
        # Update status
        applicant_id = st.number_input("Chọn ID ứng viên để cập nhật trạng thái", min_value=1, step=1)
        new_status = st.selectbox("Trạng thái mới", options=['pending', 'interview', 'hired'])
        
        if st.button("Cập nhật trạng thái"):
            try:
                applicant = Applicant.objects.get(id=applicant_id)
                applicant.status = new_status
                applicant.save()
                st.success(f"Đã cập nhật trạng thái của {applicant.name} thành {new_status}")
            except Applicant.DoesNotExist:
                st.error("Không tìm thấy ứng viên với ID đã chọn.")
            except Exception as e:
                st.error(f"Lỗi khi cập nhật: {str(e)}")
    except Exception as e:
        st.error(f"Lỗi khi tải danh sách ứng viên: {str(e)}")

# Main app
def main():
    st.sidebar.title("Trang quản lý tuyển dụng")
    page = st.sidebar.radio("Chọn chức năng", [
        "Danh sách công việc", 
        "Ứng tuyển", 
        "Thêm công việc mới", 
        "Quản lý ứng viên"
    ])
    
    if page == "Danh sách công việc":
        job_list()
    elif page == "Ứng tuyển":
        apply_job()
    elif page == "Thêm công việc mới":
        add_job()
    elif page == "Quản lý ứng viên":
        view_applicants()

if __name__ == "__main__":
    main()