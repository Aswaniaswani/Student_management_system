from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view),
    
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('register/admin/', views.register_user),
    path('add-course/admin/', views.add_course),
    path('teacher/admin/edit/<str:id>/', views.edit_teacher, name='edit_teacher'),
    path('teacher/admin/delete/<str:id>/', views.delete_teacher, name='delete_teacher'),
    path('student/admin/edit/<str:id>/', views.edit_student, name='edit_student'),
    path('student/admin/delete/<str:id>/', views.delete_student, name='delete_student'),
    path('assign-teacher/admin/', views.assign_teacher_to_course,name='assign_teacher_to_course'),
    path('assign-students/admin/', views.assign_students_to_course,name='assign_students_to_course'),
    path('view-attendance/admin/', views.admin_view_attendance,name='admin_view_attendance'),
    path('view-marks/admin/', views.admin_view_marks,name='admin_view_marks'),

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/view-attendance/', views.teacher_view_attendance, name='teacher_view_attendance'),
    path('teacher/marks/', views.teacher_marks, name='teacher_marks'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses,name='student_courses'),
    path('student/attendance/', views.student_attendance,name='student_attendance'),
    
]