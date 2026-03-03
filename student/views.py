from django.shortcuts import render, redirect 
from django.conf import settings
from bson.objectid import ObjectId
from .utils import get_db, hash_password, verify_password


# ---------- ROLE CHECK ----------
def require_role(request, roles):
    if 'role' not in request.session:
        return False
    return request.session['role'] in roles


# ---------- LOGIN ----------
def login_view(request):
    if request.method == 'POST':
        db, _ = get_db()
        user = db.users.find_one({'username': request.POST['username']})

        if user and verify_password(request.POST['password'], user['password']):
            request.session['user_id'] = str(user['_id'])
            request.session['username'] = user['username']
            request.session['role'] = user['role']
            request.session['ref_id'] = str(user['ref_id'])

            if user['role'] == 'admin':
                return redirect('admin_dashboard')
            elif user['role'] == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')

# ===================== ADMIN =====================

def admin_dashboard(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    db, _ = get_db()

    # ---------- Teachers ----------
    teachers = []
    for t in db.teachers.find():
        t['id'] = str(t['_id'])
        teachers.append(t)

    # ---------- Students ----------
    students = []
    for s in db.students.find():
        s['id'] = str(s['_id'])
        students.append(s)

    # ---------- Courses (JOIN teacher name) ----------
    courses = []
    for c in db.courses.find():
        teacher_name = "Not Assigned"

        if c.get('teacher_id'):
            teacher = db.teachers.find_one({
                '_id': ObjectId(c['teacher_id'])
            })
            if teacher:
                teacher_name = teacher['name']

        courses.append({
            'course_name': c['course_name'],
            'teacher_name': teacher_name
        })

    return render(request, 'admin/dashboard.html', {
        'teachers': teachers,
        'students': students,
        'courses': courses
    })

def register_user(request):
    if not require_role(request, ['admin']):
        return redirect('login')

    if request.method == 'POST':
        db, _ = get_db()
        role = request.POST['role']

        if role == 'student':
            ref_id = db.students.insert_one({
                'name': request.POST['name'],
                'email': request.POST['email']
            }).inserted_id

        elif role == 'teacher':
            ref_id = db.teachers.insert_one({
                'name': request.POST['name'],
                'email': request.POST['email']
            }).inserted_id
        else:
            return redirect('admin_dashboard')

        db.users.insert_one({
            'username': request.POST['username'],
            'password': hash_password(request.POST['password']),
            'role': role,
            'ref_id': ref_id
        })

        return redirect('admin_dashboard')

    return render(request, 'admin/register.html')


def add_course(request):
    if not require_role(request, ['admin']):
        return redirect('login')

    if request.method == 'POST':
        db, _ = get_db()
        db.courses.insert_one({
            'course_name': request.POST['course_name'],
            'teacher_id': None
        })
        return redirect('admin_dashboard')

    return render(request, 'admin/add_course.html')

# def assign_teacher_to_course(request):
#     if not require_role(request, ['admin']):
#         return redirect('login')

#     db, _ = get_db()

#     if request.method == 'POST':
#         course_id = ObjectId(request.POST['course_id'])
#         teacher_id = ObjectId(request.POST['teacher_id'])

#         db.courses.update_one(
#             {'_id': course_id},
#             {'$set': {'teacher_id': teacher_id}}
#         )
#         return redirect('admin_dashboard')

#     teachers = list(db.teachers.find())
#     courses = list(db.courses.find())

#     return render(request, 'admin/assign_teacher.html', {
#         'teachers': teachers,
#         'courses': courses
#     })

def assign_teacher_to_course(request):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()

    if request.method == 'POST':
        course_id = ObjectId(request.POST['course_id'])
        teacher_id = ObjectId(request.POST['teacher_id'])

        db.courses.update_one(
            {'_id': course_id},
            {'$set': {'teacher_id': teacher_id}}
        )
        return redirect('admin_dashboard')

    # ✅ convert _id → id
    teachers = []
    for t in db.teachers.find():
        t['id'] = str(t['_id'])
        teachers.append(t)

    courses = []
    for c in db.courses.find():
        c['id'] = str(c['_id'])
        courses.append(c)

    return render(request, 'admin/assign_teacher.html', {
        'teachers': teachers,
        'courses': courses
    })

# def assign_students_to_course(request):
#     if not require_role(request, ['admin']):
#         return redirect('login')

#     db, _ = get_db()

#     if request.method == 'POST':
#         course_id = ObjectId(request.POST['course_id'])
#         student_ids = request.POST.getlist('students')

#         for sid in student_ids:
#             db.enrollments.update_one(
#                 {
#                     'course_id': course_id,
#                     'student_id': ObjectId(sid)
#                 },
#                 {'$set': {'course_id': course_id, 'student_id': ObjectId(sid)}},
#                 upsert=True
#             )
#         return redirect('admin_dashboard')

#     courses = list(db.courses.find())
#     students = list(db.students.find())

#     return render(request, 'admin/assign_students.html', {
#         'courses': courses,
#         'students': students
#     })

def assign_students_to_course(request):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()

    if request.method == 'POST':
        course_id = ObjectId(request.POST['course_id'])
        student_ids = request.POST.getlist('students')

        for sid in student_ids:
            db.enrollments.update_one(
                {
                    'course_id': course_id,
                    'student_id': ObjectId(sid)
                },
                {'$set': {'course_id': course_id, 'student_id': ObjectId(sid)}},
                upsert=True
            )
        return redirect('admin_dashboard')

    courses = []
    for c in db.courses.find():
        c['id'] = str(c['_id'])
        courses.append(c)

    students = []
    for s in db.students.find():
        s['id'] = str(s['_id'])
        students.append(s)

    return render(request, 'admin/assign_students.html', {
        'courses': courses,
        'students': students
    })

def admin_view_attendance(request):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()
    records = []

    for a in db.attendance.find():
        sid = a.get('student_id')
        cid = a.get('course_id')

        if isinstance(sid, str):
            sid = ObjectId(sid)
        if isinstance(cid, str):
            cid = ObjectId(cid)

        student = db.students.find_one({'_id': sid})
        course = db.courses.find_one({'_id': cid})

        records.append({
            'student_name': student['name'] if student else 'NOT FOUND',
            'course_name': course['course_name'] if course else 'NOT FOUND',
            'date': a.get('date'),
            'present': a.get('present', False)
        })

    return render(request, 'admin/view_attendance.html', {
        'records': records
    })

def admin_view_marks(request):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()
    records = list(db.marks.find())

    return render(request, 'admin/view_marks.html', {
        'records': records
    })


# ===================== TEACHER =====================

def teacher_dashboard(request):
    if not require_role(request, ['teacher']):
        return redirect('login')

    db, _ = get_db()
    teacher_id = ObjectId(request.session['ref_id'])

    courses = list(db.courses.find({'teacher_id': teacher_id}))
    for c in courses:
        c['id'] = str(c['_id'])

    return render(request, 'teacher/dashboard.html', {'courses': courses})


# def mark_attendance(request, course_id):
#     if not require_role(request, ['teacher']):
#         return redirect('login')

#     db, _ = get_db()

#     enrollments = list(db.enrollments.find({'course_id': ObjectId(course_id)}))
#     students = list(db.students.find({
#         '_id': {'$in': [e['student_id'] for e in enrollments]}
#     }))

#     if request.method == 'POST':
#         for s in students:
#             db.attendance.insert_one({
#                 'student_id': s['_id'],
#                 'course_id': ObjectId(course_id),
#                 'date': request.POST['date'],
#                 'present': request.POST.get(str(s['_id'])) == 'on'
#             })
#         return redirect('teacher_dashboard')

#     return render(request, 'teacher/attendance.html', {
#         'students': students
#     })

def mark_attendance(request):
    if request.session.get('role') != 'teacher':
        return redirect('login')

    db, _ = get_db()
    teacher_id = ObjectId(request.session['ref_id'])

    # -------- Courses assigned to this teacher --------
    courses = []
    for c in db.courses.find({'teacher_id': teacher_id}):
        courses.append({
            'id': str(c['_id']),
            'name': c['course_name']
        })

    students = []
    selected_course_id = None

    # -------- LOAD STUDENTS --------
    if request.method == 'POST' and 'load_students' in request.POST:
        selected_course_id = request.POST.get('course_id')

        enrolls = db.enrollments.find({
            'course_id': ObjectId(selected_course_id)
        })

        student_ids = [e['student_id'] for e in enrolls]

        for s in db.students.find({'_id': {'$in': student_ids}}):
            students.append({
                'id': str(s['_id']),
                'name': s['name']
            })

    # -------- SAVE ATTENDANCE --------
    elif request.method == 'POST' and 'save_attendance' in request.POST:
        course_id = ObjectId(request.POST.get('course_id'))
        date = request.POST.get('date')
        present_students = request.POST.getlist('present_students')

        enrolls = db.enrollments.find({'course_id': course_id})

        for e in enrolls:
            student_id = e['student_id']
            db.attendance.insert_one({
                'student_id': student_id,        # ObjectId
                'course_id': course_id,          # ObjectId
                'date': date,
                'present': str(student_id) in present_students
            })

        return redirect('teacher_view_attendance')

    return render(request, 'teacher/mark_attendance.html', {
        'courses': courses,
        'students': students,
        'selected_course_id': selected_course_id
    })

def add_marks(request, course_id):
    if not require_role(request, ['teacher']):
        return redirect('login')

    if request.method == 'POST':
        db, _ = get_db()
        db.marks.update_one(
            {
                'student_id': ObjectId(request.POST['student_id']),
                'course_id': ObjectId(course_id)
            },
            {'$set': {'marks': int(request.POST['marks'])}},
            upsert=True
        )
        return redirect('teacher_dashboard')
    
def edit_teacher(request, id):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()
    teacher = db.teachers.find_one({'_id': ObjectId(id)})

    if request.method == 'POST':
        db.teachers.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': request.POST['name'],
                'email': request.POST['email']
            }}
        )
        return redirect('admin_dashboard')

    return render(request, 'admin/edit_teacher.html', {'teacher': teacher})
    
def delete_teacher(request, id):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()
    db.teachers.delete_one({'_id': ObjectId(id)})
    return redirect('admin_dashboard')

# def teacher_course_students(request, course_id):
#     if not require_role(request, ['teacher']):
#         return redirect('login')

#     db, _ = get_db()

#     enrolls = list(db.enrollments.find({'course_id': ObjectId(course_id)}))
#     student_ids = [e['student_id'] for e in enrolls]

#     students = list(db.students.find({'_id': {'$in': student_ids}}))

#     return render(request, 'teacher/students.html', {
#         'students': students
#     })

# def teacher_view_attendance(request, course_id):
#     if not require_role(request, ['teacher']):
#         return redirect('login')

#     db, _ = get_db()

#     records = list(db.attendance.find({'course_id': ObjectId(course_id)}))

#     return render(request, 'teacher/view_attendance.html', {
#         'records': records
#     })

# def teacher_view_attendance(request):
#     if not require_role(request, ['teacher']):
#         return redirect('login')

#     db, _ = get_db()
#     teacher_id = ObjectId(request.session['ref_id'])

#     records = list(db.attendance.find())

#     # replace ids with names
#     for r in records:
#         student = db.students.find_one({'_id': r['student_id']})
#         course = db.courses.find_one({'_id': r['course_id']})
#         r['student_name'] = student['name']
#         r['course_name'] = course['course_name']

#     return render(request, 'teacher/view_attendance.html', {'records': records})

def teacher_view_attendance(request):
    if request.session.get('role') != 'teacher':
        return redirect('login')

    db, _ = get_db()
    records = []

    for a in db.attendance.find():

        sid = a.get('student_id')
        cid = a.get('course_id')

        if isinstance(sid, str):
            sid = ObjectId(sid)
        if isinstance(cid, str):
            cid = ObjectId(cid)

        student = db.students.find_one({'_id': sid})
        course = db.courses.find_one({'_id': cid})

        records.append({
            'student_name': student['name'] if student else 'NOT FOUND',
            'course_name': course['course_name'] if course else 'NOT FOUND',
            'date': a.get('date'),
            'present': a.get('present', False)
        })

    return render(request, 'teacher/view_attendance.html', {
        'records': records
    })

# def teacher_marks(request):
#     if not require_role(request, ['teacher']):
#         return redirect('login')

#     db, _ = get_db()
#     teacher_id = ObjectId(request.session['ref_id'])

#     courses = list(db.courses.find({'teacher_id': teacher_id}))
#     students = list(db.students.find())

#     if request.method == 'POST':
#         db.marks.update_one(
#             {
#                 'student_id': ObjectId(request.POST['student_id']),
#                 'course_id': ObjectId(request.POST['course_id'])
#             },
#             {'$set': {'marks': int(request.POST['marks'])}},
#             upsert=True
#         )
#         return redirect('teacher_marks')

#     records = list(db.marks.find())
#     for r in records:
#         r['student_name'] = db.students.find_one({'_id': r['student_id']})['name']
#         r['course_name'] = db.courses.find_one({'_id': r['course_id']})['course_name']

#     return render(request, 'teacher/marks.html', {
#         'courses': courses,
#         'students': students,
#         'records': records
#     })
def teacher_marks(request):
    if not require_role(request, ['teacher']):
        return redirect('login')

    db, _ = get_db()
    teacher_id = ObjectId(request.session['ref_id'])

    courses = []
    for c in db.courses.find({'teacher_id': teacher_id}):
        c['id'] = str(c['_id'])   # ✅
        courses.append(c)

    students = []
    for s in db.students.find():
        s['id'] = str(s['_id'])   # ✅
        students.append(s)

    if request.method == 'POST':
        db.marks.update_one(
            {
                'student_id': ObjectId(request.POST['student_id']),
                'course_id': ObjectId(request.POST['course_id'])
            },
            {'$set': {'marks': int(request.POST['marks'])}},
            upsert=True
        )
        return redirect('teacher_marks')

    records = []
    for r in db.marks.find():
        student = db.students.find_one({'_id': r['student_id']})
        course = db.courses.find_one({'_id': r['course_id']})
        records.append({
            'student_name': student['name'],
            'course_name': course['course_name'],
            'marks': r['marks']
        })

    return render(request, 'teacher/marks.html', {
        'courses': courses,
        'students': students,
        'records': records
    })

# ===================== STUDENT =====================

def student_dashboard(request):
    if request.session.get('role') != 'student':
        return redirect('login')

    db, _ = get_db()
    student_id = ObjectId(request.session['ref_id'])

    # ---------------- ATTENDANCE % ----------------
    total = db.attendance.count_documents({
        'student_id': student_id
    })

    present = db.attendance.count_documents({
        'student_id': student_id,
        'present': True
    })

    attendance_percent = 0
    if total > 0:
        attendance_percent = round((present / total) * 100)

    # ---------------- MARKS ----------------
    marks = []

    for m in db.marks.find({'student_id': student_id}):
        course = db.courses.find_one({'_id': m['course_id']})

        marks.append({
            'course_name': course['course_name'],
            'marks': m['marks']
        })

    return render(request, 'student/dashboard.html', {
        'attendance': attendance_percent,
        'marks': marks
    })

def edit_student(request, id):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()
    student = db.students.find_one({'_id': ObjectId(id)})

    if request.method == 'POST':
        db.students.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name': request.POST['name'],
                'email': request.POST['email']
            }}
        )
        return redirect('admin_dashboard')

    return render(request, 'admin/edit_student.html', {'student': student})

def delete_student(request, id):
    if not require_role(request, ['admin']):
        return redirect('login')

    db, _ = get_db()
    db.students.delete_one({'_id': ObjectId(id)})
    return redirect('admin_dashboard')

def student_courses(request):
    if not require_role(request, ['student']):
        return redirect('login')

    db, _ = get_db()
    student_id = ObjectId(request.session['ref_id'])

    enrolls = list(db.enrollments.find({'student_id': student_id}))
    course_ids = [e['course_id'] for e in enrolls]

    courses = list(db.courses.find({'_id': {'$in': course_ids}}))

    return render(request, 'student/courses.html', {
        'courses': courses
    })

def student_attendance(request):
    if not require_role(request, ['student']):
        return redirect('login')

    db, _ = get_db()
    student_id = ObjectId(request.session['ref_id'])

    pipeline = [
        {'$match': {'student_id': student_id}},
        {'$group': {
            '_id': '$course_id',
            'total': {'$sum': 1},
            'present': {'$sum': {'$cond': ['$present', 1, 0]}}
        }},
        {'$project': {
            'percentage': {
                '$multiply': [{'$divide': ['$present', '$total']}, 100]
            }
        }}
    ]

    data = list(db.attendance.aggregate(pipeline))

    return render(request, 'student/attendance.html', {
        'data': data
    })


