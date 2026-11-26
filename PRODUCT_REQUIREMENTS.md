# School LMS — Product Requirements

**Status:** Initial draft for review  
**Version:** 1.0  
**Date:** 25 November 2026

## 1. Product overview

A learning management system for multiple secondary schools, serving students aged 12 and above. Each school manages its own users, academic structure, learning activities, and student records. A parent or guardian may have children attending different schools and use one account to view each child's approved progress.

## 2. Goals for the first release

The first release should allow schools to:

1. Manage academic years, terms, year levels/forms, classes, subjects, and enrollments.
2. Share lessons and learning materials with a class.
3. Create assignments and collect student submissions as typed text or file uploads.
4. Record and share grades and teacher feedback.
5. Record student attendance.
6. Give approved parents/guardians access to their linked child's grades, attendance, and feedback.

## 3. User roles and access

### Platform administrator

- Creates and manages schools on the platform.
- Supports school administrators and platform-level operations.
- Does not automatically receive access to school learning records unless a separate operational need and permission are defined.

### School administrator

- Manages users and assigns school roles.
- Manages academic years, terms, year levels/forms, classes, subjects, enrollments, and teacher assignments.
- Imports student and staff records from a spreadsheet.
- Reviews student registration requests and parent/guardian link requests.
- Can correct or revoke a parent/student relationship and associated access.

### Teacher

- Belongs to exactly one school.
- Can access only classes and students assigned to them.
- Shares lessons, creates assignments, reviews submissions, records grades and feedback, and records attendance for assigned classes.

### Student

- Belongs to one school after enrollment is approved.
- Can view their own classes, lessons, assignments, attendance, grades, and feedback.
- Can submit assignment text and file attachments.
- May register for an account, but must be approved and matched to school enrollment before seeing school records.

### Parent or guardian

- May have children attending multiple schools, linked to one parent account.
- Can see only approved linked children’s grades, attendance, and teacher feedback.
- Cannot access lessons, assignments, other students’ records, or school administration functions unless separately assigned a role by that school.

## 4. School data separation

- Every school-owned record must be associated with a school.
- School users may access records only within their school and according to their role and assignments.
- A teacher belongs to one school.
- Parent accounts may be linked to students in more than one school, while the parent view remains limited to the explicitly approved children and the permitted progress fields.
- Authorization checks must be enforced by the API, not only by the user interface.

## 5. Academic structure (recommended starting model)

Use the following hierarchy. Labels can be configured to match each school’s terminology (for example, “year”, “grade”, or “form”).

1. **School** — the tenant boundary for school data.
2. **Academic year** — for example, the school’s 2026–2027 year.
3. **Term** — one or more terms within an academic year, with dates set by the school.
4. **Year level/form** — the student cohort or level, such as Year 8 or Form 2.
5. **Class group/section** — the roster of students who progress together, such as Year 8 Blue.
6. **Subject offering** — a subject taught to a class group for a specific academic year/term, with one or more assigned teachers if the school needs that.
7. **Enrollment** — a student’s membership in a class group and subject offering, with effective dates/status so transfers and withdrawals can be recorded.

Lessons, assignments, submissions, attendance, grades, and feedback should be attached to the relevant subject offering and academic period. This makes it possible for the same student to take different subjects and teachers to teach multiple offerings while keeping records tied to the correct year and class.

**Initial assumption:** A student has one main class group per academic year and enrolls in subject offerings within that year. The model should allow a school to change a student’s class or subject enrollment without overwriting historical records.

## 6. Key workflows

### 6.1 School setup and bulk import

1. Platform administrator creates a school and its first school administrator.
2. School administrator configures academic year, terms, year levels/forms, class groups, and subjects.
3. Administrator imports students and staff using a provided spreadsheet template, or creates records individually.
4. The system validates rows and reports errors before committing the import.
5. Invitations are sent to users where contact details are available; accounts are activated through a secure invitation flow.

### 6.2 Student self-registration

1. Student registers with basic account details and provides a school-issued invitation or registration code.
2. The account and school-join request remain pending.
3. School administrator verifies the student against school enrollment records and approves or rejects the request.
4. The student receives access only after approval and assignment to the correct school/class.

A registration code identifies a school or invite cohort; it must not by itself grant access to student data or allow a person to assign themselves a privileged role.

### 6.3 Parent/guardian linking

1. School staff record the parent/guardian relationship using the school’s existing records.
2. The school sends an invitation to the contact information it has on file.
3. The parent verifies control of that email address or phone number and creates/signs into an account.
4. The link remains pending until a school administrator approves it.
5. After approval, the parent can view only that linked child’s grades, attendance, and teacher feedback.
6. The school can review, correct, or revoke the link; changes are recorded in an audit trail.

A single parent account may accept approved links from different schools for children attending those schools.

### 6.4 Teacher lesson and assignment workflow

1. Teacher opens an assigned subject offering.
2. Teacher publishes a lesson/material or creates an assignment with instructions, due date, and optional attachments.
3. Students enrolled in that offering can view the published item.
4. A student submits typed text, one or more allowed files, or both, before or after the due date according to school policy.
5. Teacher reviews the submission and records a grade and feedback.
6. Student sees their own grade and feedback; an approved parent sees those fields for their linked child.

### 6.5 Attendance workflow

1. Teacher selects an assigned class/subject offering and date.
2. Teacher records each enrolled student’s attendance status.
3. Changes are attributable to the staff member and timestamped.
4. Students and approved parents can view the student’s own attendance history.

## 7. Functional requirements

### School and academic setup

- **SCH-01:** Platform administrator can create and manage schools.
- **SCH-02:** School administrator can manage the school’s academic years and terms.
- **SCH-03:** School administrator can configure year levels/forms, class groups, subjects, and teacher assignments.
- **SCH-04:** School administrator can enroll, transfer, and withdraw students while retaining historical records.
- **SCH-05:** School administrator can import students and staff from a spreadsheet and review validation errors before import.

### Accounts and access

- **AUTH-01:** School administrators create accounts and assign roles within their school.
- **AUTH-02:** Students can self-register, but their school access remains pending until approved by a school administrator.
- **AUTH-03:** A teacher can be associated with only one school.
- **AUTH-04:** A user can have a parent/guardian account linked to multiple students across multiple schools.
- **AUTH-05:** Every protected operation checks both role and school/resource assignment.
- **AUTH-06:** The system records administrator decisions and changes to role, enrollment, and guardian links.

### Lessons and assignments

- **LEARN-01:** Teacher can publish lessons/materials to assigned subject offerings.
- **ASSIGN-01:** Teacher can create an assignment for an assigned subject offering.
- **ASSIGN-02:** Students enrolled in the offering can submit typed text and file uploads.
- **ASSIGN-03:** System records submission time and retains submission history when resubmission is allowed.
- **ASSIGN-04:** Teacher can review submissions and record a grade and feedback.

### Grades, feedback, and attendance

- **PROG-01:** Student can view only their own grades, attendance, and feedback.
- **PROG-02:** Approved parent/guardian can view only grades, attendance, and feedback for linked children.
- **ATT-01:** Teacher can record attendance for assigned offerings/classes.
- **ATT-02:** Attendance changes include the responsible user and timestamp.

## 8. Initial data concepts

- School
- User account and school membership/role
- Academic year and term
- Year level/form
- Class group/section
- Subject
- Subject offering and teacher assignment
- Student enrollment
- Parent/guardian relationship and approval status
- Lesson/material
- Assignment and attachment
- Submission and uploaded file
- Grade and feedback
- Attendance record
- Invitation/registration request
- Audit event

A person’s login account should be distinct from their school-specific membership and role. This supports parent access across schools while preserving school-specific permissions.

## 9. Security, privacy, and operational requirements

- Use secure password storage and authenticated access.
- Apply role-based and school-scoped authorization to every API operation.
- Use expiring, single-use invitation tokens and one-time verification codes; do not store the raw token/code after validation.
- Restrict file type and size, store uploads outside public web paths, and authorize every download.
- Keep audit records for account approval, role changes, enrollment changes, guardian-link approval/revocation, grade changes, and attendance changes.
- Collect only the information needed to operate the school service; define retention and deletion rules before production launch.
- Protect student information in logs, exports, backups, and support workflows.
- Confirm applicable privacy, child-data, consent, data residency, and retention requirements for the countries where schools operate before production launch. If the initial deployment is in Nigeria, review the Nigeria Data Protection Act 2023 and applicable NDPC guidance with a qualified local privacy contact.

## 10. Open decisions

These affect detailed implementation and should be decided before the related feature is built:

1. Which country/countries will the first schools operate in?
2. Should a student use a school-issued invitation, a short-lived registration code, or either method?
3. What class/year terminology and grading scales should each school configure?
4. Are assignments allowed to be late, and can students resubmit? Can teachers set these rules per assignment?
5. Which submission file types and maximum sizes should be allowed?
6. What attendance statuses are required (for example, present, absent, late, excused)?
7. Should grades be hidden from students/parents until a teacher publishes them?
8. What notification channels are required for invitations, new assignments, grades, and attendance? *(Decided: **Resend** will be used for transactional email notifications; SMS and in-app notifications remain open to decide if needed.)*
9. What hosting, backup, expected user volume, and availability targets are required?

## 11. Suggested AI-assisted build process

Work in small vertical slices. For each slice, give the coding assistant the relevant requirement IDs and acceptance criteria, ask it to inspect the existing project and propose the change, then implement and review one slice at a time.

Suggested order:

1. FastAPI project foundation, configuration, database connection, and health endpoint.
2. School and account foundation, authentication, memberships, roles, and school-scoped authorization.
3. Academic years, terms, class groups, subjects, offerings, enrollments, and spreadsheet import.
4. Student registration requests and approval.
5. Parent invitations, verification, approval, and multi-school child links.
6. Lessons and file storage.
7. Assignments, text/file submissions, and resubmission rules.
8. Grades, feedback, and student/parent views.
9. Attendance and history.
10. Deployment, backups, monitoring, and privacy review.

For each slice, ask the AI to:

- State assumptions and list files it plans to change before editing.
- Implement only the selected requirements.
- Include database migrations and focused automated checks for the changed behavior.
- Explain authorization checks and edge cases.
- Review its own diff against the acceptance criteria and report anything still incomplete.

Keep the requirements document updated when decisions change. Do not move on from a slice until its acceptance criteria are met and the changes are understandable to you.
