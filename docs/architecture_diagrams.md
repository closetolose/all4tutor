# All4Tutors — Architecture Diagrams

This document contains Mermaid diagrams describing the All4Tutors Django project architecture. The project is a tutoring management platform with roles for tutors, students, and admins.

---

## 1. System Architecture

High-level deployment overview: Docker services, reverse proxy, application server, database, and background jobs.

```mermaid
flowchart TB
    subgraph External["External"]
        Client[Client Browser]
    end

    subgraph Docker["Docker Compose"]
        subgraph Nginx["nginx (reverse proxy)"]
            NginxSvc[nginx:80/443]
        end

        subgraph Web["web (Django)"]
            Gunicorn[Gunicorn :8000]
            Django[Django App]
            CoreApp[core app]
        end

        subgraph DB["db (MySQL)"]
            MySQL[(MySQL 8.0 :3306)]
        end

        subgraph Cron["cron (scheduler)"]
            CronJob[cron -f]
            SendReminders[send_reminders<br/>*/5 * * * *]
            CheckOverdue[check_overdue_homeworks<br/>*/5 * * * *]
        end

        subgraph Bot["bot (Telegram)"]
            BotPolling[bot_polling.py]
        end
    end

    subgraph Volumes["Shared Volumes"]
        StaticVol[static_volume]
        MediaVol[media_volume]
        MySQLData[mysql_data]
    end

    Client -->|HTTP/HTTPS| NginxSvc
    NginxSvc -->|proxy_pass| Gunicorn
    Gunicorn --> Django
    Django --> CoreApp
    CoreApp --> MySQL
    CronJob --> SendReminders
    CronJob --> CheckOverdue
    SendReminders --> MySQL
    CheckOverdue --> MySQL
    BotPolling --> MySQL
    Django --> StaticVol
    Django --> MediaVol
    NginxSvc --> StaticVol
    NginxSvc --> MediaVol
    MySQL --> MySQLData

    style NginxSvc fill:#e1f5fe
    style Gunicorn fill:#fff3e0
    style MySQL fill:#e8f5e9
    style CronJob fill:#f3e5f5
```

**Components:**
- **nginx** — Reverse proxy, serves static/media, SSL termination (Certbot)
- **web** — Gunicorn + Django (3 workers, 120s timeout)
- **db** — MySQL 8.0 (`tutor_db`)
- **cron** — Runs `send_reminders` and `check_overdue_homeworks` every 5 minutes
- **bot** — Telegram bot polling for notifications

---

## 2. Data Model (Entity Relationship)

Key models and their relationships.

```mermaid
erDiagram
    AUTH_USER ||--|| Users : "profile"
    Users ||--o{ ConnectionRequest : "tutor"
    Users ||--o{ ConnectionRequest : "student"
    Users ||--o{ StudyGroups : "tutor"
    Users }o--o{ StudyGroups : "students"
    Users ||--o{ Subjects : "subjects"
    Subjects ||--o{ StudyGroups : "subject"
    StudyGroups ||--o{ Lessons : "group"
    Users ||--o{ Lessons : "tutor"
    Users ||--o{ Lessons : "student"
    Subjects ||--o{ Lessons : "subject"
    Lessons ||--o{ LessonAttendance : "attendances"
    Users ||--o{ LessonAttendance : "student"
    LessonAttendance ||--o| Transaction : "attendance"
    Users ||--o{ Transaction : "student"
    Users ||--o{ Transaction : "tutor"
    Users ||--o{ StudentBalance : "tutor"
    Users ||--o{ StudentBalance : "student"
    Users ||--o{ Homework : "tutor"
    Users ||--o{ Homework : "student"
    Subjects ||--o{ Homework : "subject"
    Homework ||--o{ HomeworkResponse : "responses"
    Users ||--o{ HomeworkResponse : "student"
    FilesLibrary }o--o{ Homework : "files"
    Users ||--o{ FilesLibrary : "tutor"
    FileTag }o--o{ FilesLibrary : "tags"
    Users ||--o{ FileTag : "tutor"
    Lessons }o--o{ FilesLibrary : "materials"
    Users ||--o{ PaymentReceipt : "student"
    Users ||--o{ PaymentReceipt : "tutor"
    Users ||--o{ UnlinkRequest : "student"
    Users ||--o{ UnlinkRequest : "tutor"
    AUTH_USER ||--o| UnlinkRequest : "reviewed_by"
    AUTH_USER ||--o{ Notification : "user"
    Users ||--o{ TutorStudentNote : "tutor"
    Users ||--o{ TutorStudentNote : "student"
    Users ||--o{ TestResult : "tutor"
    Users ||--o{ TestResult : "student"
    Subjects ||--o{ TestResult : "subject"
    Users ||--o{ UserGroupColor : "user"
    StudyGroups ||--o{ UserGroupColor : "group"
    Users ||--o{ StudentTariff : "tutor"
    Users ||--o{ StudentTariff : "student"
    StudyGroups ||--o| StudentTariff : "group"
    Subjects ||--o{ StudentTariff : "subject"

    AUTH_USER {
        int id PK
        string username
        string email
        bool is_active
    }

    Users {
        int id PK
        int user_id FK
        string role
        string first_name
        string last_name
        string timezone
        string telegram_id
    }

    ConnectionRequest {
        int id PK
        int tutor_id FK
        int student_id FK
        string status
        string color_hex
        string tutor_color_hex
    }

    StudyGroups {
        int id PK
        int tutor_id FK
        int subject_id FK
        string name
    }

    Subjects {
        int id PK
        int tutor_id FK
        string name
    }

    Lessons {
        int id PK
        int tutor_id FK
        int student_id FK
        int group_id FK
        int subject_id FK
        datetime start_time
        datetime end_time
        decimal price
    }

    LessonAttendance {
        int id PK
        int lesson_id FK
        int student_id FK
        bool was_present
        bool is_paid
    }

    Homework {
        int id PK
        int tutor_id FK
        int student_id FK
        int subject_id FK
        string status
        datetime deadline
    }

    FilesLibrary {
        int id PK
        int tutor_id FK
        file file
        string file_name
    }

    FileTag {
        int id PK
        int tutor_id FK
        string name
    }

    PaymentReceipt {
        int id PK
        int student_id FK
        int tutor_id FK
        decimal amount
        string status
    }

    Notification {
        int id PK
        int user_id FK
        string message
        string link
        bool is_read
    }
```

**Simplified relationship summary:**

| Entity | Key Relationships |
|--------|-------------------|
| **Users** | 1:1 with Auth User; tutor/student; owns Lessons, Homework, FilesLibrary, Subjects |
| **ConnectionRequest** | Links tutor ↔ student (pending/confirmed/rejected/archived) |
| **StudyGroups** | tutor, subject; M2M students |
| **Lessons** | tutor, student, group, subject; M2M materials (FilesLibrary) |
| **LessonAttendance** | lesson, student; drives Transaction, StudentBalance |
| **Homework** | tutor, student, subject; M2M files; has HomeworkResponse |
| **PaymentReceipt** | student → tutor; approve creates Transaction + StudentBalance |

---

## 3. User Flow

How tutors and students interact with the system.

```mermaid
flowchart TB
    subgraph Auth["Authentication"]
        Login[Login]
        Register[Register]
        EditProfile[Edit Profile]
    end

    subgraph Tutor["Tutor Flow"]
        TMyStudents[My Students]
        TAddStudent[Add Student]
        TConfirmations[Confirmations]
        TAddLesson[Add Lesson]
        TEditLesson[Edit Lesson]
        TCreateGroup[Create Group]
        TGroupCard[Group Card]
        TFilesLibrary[Files Library]
        TAddHomework[Add Homework]
        TFinances[Finances]
        TResults[Results]
        TApproval[Approve Receipts]
    end

    subgraph Student["Student Flow"]
        SMyTutors[My Tutors]
        STutorCard[Tutor Card]
        SConfirmations[Confirmations]
        SMyAssignments[My Assignments]
        SSubmitHW[Submit Homework]
        SPaymentReceipts[Payment Receipts]
        SSubmitReceipt[Submit Receipt]
    end

    subgraph Shared["Shared"]
        Index[Index / Dashboard]
        Lessons[Lessons List]
        HomeworkDetail[Homework Detail]
    end

    subgraph Admin["Admin"]
        AdminDashboard[Dashboard Admin]
        UnlinkRequests[Unlink Requests]
    end

    Login --> Index
    Register --> EditProfile
    EditProfile --> Index

    Index --> TMyStudents
    Index --> Lessons
    TAddStudent -->|ConnectionRequest| TConfirmations
    TMyStudents --> TAddStudent
    TMyStudents --> TAddLesson
    TMyStudents --> TCreateGroup
    TMyStudents --> TGroupCard
    TAddLesson --> Lessons
    TCreateGroup --> TGroupCard
    TGroupCard --> TAddHomework
    TFilesLibrary --> TAddHomework
    TAddHomework --> HomeworkDetail
    TFinances --> TApproval
    TResults --> TestResult[Test Results]

    Index --> SMyTutors
    SMyTutors --> STutorCard
    SMyTutors -->|ConnectionRequest| SConfirmations
    SMyAssignments --> SSubmitHW
    SSubmitHW --> HomeworkDetail
    SPaymentReceipts --> SSubmitReceipt
    SSubmitReceipt --> TApproval

    AdminDashboard --> UnlinkRequests
```

**Sequence: Request flow (student submits homework)**

```mermaid
sequenceDiagram
    participant Student
    participant View
    participant Homework
    participant HomeworkResponse
    participant Notification

    Student->>View: POST /homework/submit/<hw_id>/
    View->>Homework: get_object_or_404
    View->>HomeworkResponse: create(file, student)
    View->>Homework: status = 'submitted'
    View->>Student: redirect homework_detail
    Note over Student,Notification: Cron: check_overdue_homeworks
    Note over Homework,Notification: If overdue → Notification.create
```

---

## 4. Template / Rendering Architecture

Desktop vs mobile template selection via `smart_render` and `MobileDiscoveryMiddleware`.

```mermaid
flowchart TB
    subgraph Request["Request Lifecycle"]
        RequestIn[HTTP Request]
        UserAgent[User-Agent Header]
        MobileMiddleware[MobileDiscoveryMiddleware]
        RequestOut[request.is_mobile]
    end

    subgraph View["View Layer"]
        ViewFunc[View Function]
        SmartRender[smart_render]
        TemplateName[template_name: core/xxx.html]
    end

    subgraph SmartRenderLogic["smart_render Logic"]
        CheckMobile{request.is_mobile?}
        MobilePath[mobile/xxx.html]
        CorePath[core/xxx.html]
        TemplateExists{Template exists?}
    end

    subgraph Templates["Template Directories"]
        subgraph Core["core/templates/core/"]
            CoreIndex[index.html]
            CoreStudents[my_students.html]
            CoreLesson[add_lesson.html]
            CoreFiles[files_library.html]
            CoreFinances[finances.html]
        end

        subgraph Mobile["core/templates/mobile/"]
            MobileIndex[index.html]
            MobileStudents[my_students.html]
            MobileLesson[add_lesson.html]
            MobileFiles[files_library.html]
            MobileFinances[finances.html]
        end
    end

    RequestIn --> UserAgent
    UserAgent --> MobileMiddleware
    MobileMiddleware --> RequestOut
    RequestOut --> ViewFunc

    ViewFunc --> SmartRender
    SmartRender --> TemplateName
    TemplateName --> CheckMobile

    CheckMobile -->|Yes| MobilePath
    CheckMobile -->|No| CorePath

    MobilePath --> TemplateExists
    TemplateExists -->|Yes| MobileIndex
    TemplateExists -->|No| CorePath

    CorePath --> CoreIndex
```

**Mobile detection (MobileDiscoveryMiddleware):**

```mermaid
flowchart LR
    UA[User-Agent] --> Regex[regex: iphone|android|mobile|smartphone|...]
    Regex -->|Match| SetIsMobile[request.is_mobile = True]
    Regex -->|No match| SetIsMobile[request.is_mobile = False]
```

**smart_render implementation:**

```python
# core/views.py (simplified)
def smart_render(request, template_name, context=None):
    if getattr(request, 'is_mobile', False):
        mobile_template = template_name.replace('core/', 'mobile/')
        try:
            get_template(mobile_template)
            return render(request, mobile_template, context)
        except TemplateDoesNotExist:
            pass
    return render(request, template_name, context)
```

**Template parity:**

| Template | core/ | mobile/ |
|----------|-------|---------|
| index | ✓ | ✓ |
| my_students | ✓ | ✓ |
| add_lesson | ✓ | ✓ |
| my_assignments | ✓ | ✓ |
| files_library | ✓ | ✓ |
| finances | ✓ | ✓ |
| group_card | ✓ | ✓ |
| student_card | ✓ | ✓ |
| tutor_card | ✓ | ✓ |
| payment_receipts_* | ✓ | ✓ |
| ... | ... | ... |

**Context processors** (available in all templates): `notifications_processor`, `next_lesson_processor`, `breadcrumbs`.

---

## 5. Request Flow (Simplified)

```mermaid
flowchart TB
    subgraph Client["Client"]
        Browser[Browser]
    end

    subgraph Nginx["nginx"]
        Proxy[proxy_pass]
    end

    subgraph Django["Django"]
        subgraph Middleware["Middleware Stack"]
            M1[SecurityMiddleware]
            M2[SessionMiddleware]
            M3[TimezoneMiddleware]
            M4[MobileDiscoveryMiddleware]
            M5[ProfileCompletionMiddleware]
            M6[SessionCheckMiddleware]
        end

        subgraph URL["URL Router"]
            Urls[urls.py]
        end

        subgraph View["View"]
            ViewFunc[View Function]
        end

        subgraph Context["Context Processors"]
            CP1[notifications_processor]
            CP2[next_lesson_processor]
            CP3[breadcrumbs]
        end

        subgraph Render["Render"]
            SmartRender[smart_render]
        end
    end

    subgraph DB["MySQL"]
        MySQL[(Database)]
    end

    Browser -->|:80/:443| Proxy
    Proxy -->|:8000| M1
    M1 --> M2 --> M3 --> M4 --> M5 --> M6
    M6 --> Urls
    Urls --> ViewFunc
    ViewFunc --> MySQL
    ViewFunc --> CP1
    ViewFunc --> CP2
    ViewFunc --> CP3
    ViewFunc --> SmartRender
    SmartRender --> Browser
```

---

## Diagram Index

| Diagram | Purpose |
|---------|---------|
| **System Architecture** | Docker services, nginx, web, db, cron, bot |
| **Data Model** | ER diagram of core models and relationships |
| **User Flow** | Tutor and student flows |
| **Template/Rendering** | smart_render and `core/` vs `mobile/` |
| **Request Flow** | Middleware → URL → View → Context → Render |

**Assumptions:**
- Auth assumed via Django's built-in auth; `Users` extends via `User.profile`
- Admin panel: Django admin at `/secretplace/`; custom dashboard at `/dashboard/admin/`
- Telegram bot: separate polling process; `send_telegram_notification` used by cron

---

## 6. Физическая модель базы данных

```mermaid
erDiagram
    %% ===== СУЩНОСТИ =====

    auth_user {
        int id PK
        varchar username
        varchar email
        bool is_active
        bool is_superuser
        datetime date_joined
    }

    users {
        int id PK
        int user_id FK "-> auth_user (1:1)"
        varchar last_name
        varchar first_name
        varchar patronymic
        varchar role "tutor | student"
        varchar address
        varchar contact
        varchar telegram_id
        varchar timezone
        varchar school_class
        varchar parent_name
        varchar parent_phone
        uuid session_key
    }

    subjects {
        int id PK
        varchar name
        int tutor_id FK "-> users"
    }

    study_groups {
        int id PK
        varchar name
        int tutor_id FK "-> users"
        int subject_id FK "-> subjects"
    }

    group_members {
        int id PK
        int group_id FK "-> study_groups"
        int student_id FK "-> users"
    }

    lessons {
        int id PK
        int tutor_id FK "-> users"
        int subject_id FK "-> subjects"
        int student_id FK "-> users (nullable)"
        int group_id FK "-> study_groups (nullable)"
        text notes
        text homework
        datetime start_time
        datetime end_time
        int duration
        varchar format
        text location
        bool is_paid
        uuid series_id
        decimal price
        bool reminder_sent
        datetime created_at
        datetime updated_at
    }

    lesson_attendance {
        int id PK
        int lesson_id FK "-> lessons"
        int student_id FK "-> users"
        bool is_paid
        bool was_present
    }

    file_tags {
        int id PK
        int tutor_id FK "-> users"
        varchar name
    }

    files_library {
        int id PK
        int tutor_id FK "-> users"
        varchar file
        varchar file_name
        datetime upload_date
    }

    files_library_tags {
        int id PK
        int fileslibrary_id FK "-> files_library"
        int filetag_id FK "-> file_tags"
    }

    lessons_materials {
        int id PK
        int lesson_id FK "-> lessons"
        int fileslibrary_id FK "-> files_library"
    }

    student_balance {
        int id PK
        int tutor_id FK "-> users"
        int student_id FK "-> users"
        decimal balance
    }

    student_transactions {
        int id PK
        int student_id FK "-> users"
        int tutor_id FK "-> users"
        int attendance_id FK "-> lesson_attendance (nullable)"
        decimal amount
        varchar type "deposit | withdrawal"
        varchar description
        datetime date
    }

    payment_receipts {
        int id PK
        int student_id FK "-> users"
        int tutor_id FK "-> users"
        decimal amount
        date receipt_date
        varchar file
        varchar status "pending | approved | rejected"
        text comment
        datetime created_at
        datetime reviewed_at
    }

    tutor_subjects {
        int id PK
        int tutor_id FK "-> users"
        int subject_id FK "-> subjects"
    }

    connection_requests {
        int id PK
        int tutor_id FK "-> users"
        int student_id FK "-> users"
        varchar status "pending | confirmed | rejected | archived"
        datetime created_at
        varchar color_hex
        varchar tutor_color_hex
    }

    unlink_requests {
        int id PK
        int student_id FK "-> users"
        int tutor_id FK "-> users"
        varchar status "pending | approved | rejected"
        datetime created_at
        datetime reviewed_at
        int reviewed_by_id FK "-> auth_user (nullable)"
    }

    user_group_colors {
        int id PK
        int user_id FK "-> users"
        int group_id FK "-> study_groups"
        varchar color_hex
    }

    student_tariff {
        int id PK
        int tutor_id FK "-> users"
        int student_id FK "-> users (nullable)"
        int group_id FK "-> study_groups (nullable)"
        int subject_id FK "-> subjects"
        decimal price
    }

    student_performance {
        int id PK
        int student_id FK "-> users"
        int lesson_id FK "-> lessons (nullable)"
        varchar type "hw | test"
        int score
        text comment
        date date
    }

    notifications {
        int id PK
        int user_id FK "-> auth_user"
        varchar message
        varchar link
        bool is_read
        datetime created_at
        varchar type "warning | info"
    }

    homework {
        int id PK
        int tutor_id FK "-> users"
        int student_id FK "-> users"
        int subject_id FK "-> subjects"
        text description
        datetime deadline
        varchar status "pending | submitted | revision | completed | overdue"
        bool is_overdue_notified
        text tutor_comment
        datetime created_at
        datetime updated_at
    }

    homework_files {
        int id PK
        int homework_id FK "-> homework"
        int fileslibrary_id FK "-> files_library"
    }

    homework_response {
        int id PK
        int homework_id FK "-> homework"
        varchar file
        varchar file_name
        int student_id FK "-> users (nullable)"
        datetime created_at
        datetime updated_at
    }

    tutor_student_note {
        int id PK
        int tutor_id FK "-> users"
        int student_id FK "-> users"
        text text
        datetime updated_at
    }

    test_results {
        int id PK
        int tutor_id FK "-> users"
        int student_id FK "-> users"
        int subject_id FK "-> subjects"
        decimal max_score
        decimal score
        date date
        text comment
    }

    %% ===== СВЯЗИ =====

    auth_user ||--|| users : "profile"

    users ||--o{ subjects : "tutor"
    users ||--o{ study_groups : "tutor"
    subjects ||--o{ study_groups : "subject"

    study_groups ||--o{ group_members : "group"
    users ||--o{ group_members : "student"

    users ||--o{ lessons : "tutor"
    subjects ||--o{ lessons : "subject"
    users |o--o{ lessons : "student"
    study_groups |o--o{ lessons : "group"

    lessons ||--o{ lesson_attendance : "lesson"
    users ||--o{ lesson_attendance : "student"

    users ||--o{ file_tags : "tutor"
    users ||--o{ files_library : "tutor"
    files_library ||--o{ files_library_tags : "file"
    file_tags ||--o{ files_library_tags : "tag"

    lessons ||--o{ lessons_materials : "lesson"
    files_library ||--o{ lessons_materials : "file"

    users ||--o{ student_balance : "tutor"
    users ||--o{ student_balance : "student"

    users ||--o{ student_transactions : "student"
    users ||--o{ student_transactions : "tutor"
    lesson_attendance |o--o{ student_transactions : "attendance"

    users ||--o{ payment_receipts : "student"
    users ||--o{ payment_receipts : "tutor"

    users ||--o{ tutor_subjects : "tutor"
    subjects ||--o{ tutor_subjects : "subject"

    users ||--o{ connection_requests : "tutor"
    users ||--o{ connection_requests : "student"

    users ||--o{ unlink_requests : "student"
    users ||--o{ unlink_requests : "tutor"
    auth_user |o--o{ unlink_requests : "reviewer"

    users ||--o{ user_group_colors : "user"
    study_groups ||--o{ user_group_colors : "group"

    users ||--o{ student_tariff : "tutor"
    users |o--o{ student_tariff : "student"
    study_groups |o--o{ student_tariff : "group"
    subjects ||--o{ student_tariff : "subject"

    users ||--o{ student_performance : "student"
    lessons |o--o{ student_performance : "lesson"

    auth_user ||--o{ notifications : "user"

    users ||--o{ homework : "tutor"
    users ||--o{ homework : "student"
    subjects ||--o{ homework : "subject"
    homework ||--o{ homework_files : "homework"
    files_library ||--o{ homework_files : "file"

    homework ||--o{ homework_response : "homework"
    users |o--o{ homework_response : "student"

    users ||--o{ tutor_student_note : "tutor"
    users ||--o{ tutor_student_note : "student"

    users ||--o{ test_results : "tutor"
    users ||--o{ test_results : "student"
    subjects ||--o{ test_results : "subject"
```

### Условные обозначения (Crow's Foot Notation)

| Символ | Значение |
|--------|----------|
| `\|\|--\|\|` | Один к одному (1:1) |
| `\|\|--o{` | Один ко многим (1:M), обязательная связь |
| `\|o--o{` | Один ко многим, необязательная сторона (nullable FK) |
| Промежуточные таблицы | Реализация связей M:N |

### Статистика физической модели

| Показатель | Значение |
|---|---|
| Таблиц-сущностей | 23 |
| Промежуточных таблиц (M:N) | 3 (`files_library_tags`, `lessons_materials`, `homework_files`) |
| Таблиц всего | 27 (включая `auth_user`) |
| Связей FK | 48 |
| Уникальных ограничений (UNIQUE) | 9 |
