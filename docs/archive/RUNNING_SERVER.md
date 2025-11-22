# Running the Floor Management System Server

## Quick Start

### 1. **Open Terminal/Command Prompt**
Navigate to your project directory:
```bash
cd D:\PycharmProjects\floor_management_system-B
```

### 2. **Activate Virtual Environment**
```bash
source venv/Scripts/activate
```
(On Windows CMD, use: `venv\Scripts\activate`)

### 3. **Run the Server**
```bash
python manage.py runserver
```

You should see output like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 4. **Access the Application**
Open your browser and go to:
```
http://127.0.0.1:8000/
```

---

## Checking Logs & Debugging

### **1. View Server Output in Terminal**
The terminal running the server shows all logs in real-time. You should see:
- HTTP requests and responses
- Error messages
- Database queries (if DEBUG=True)
- Warning messages

Example output:
```
[14/Nov/2025 10:30:45] "GET / HTTP/1.1" 200 5234
[14/Nov/2025 10:30:46] "POST /accounts/login/ HTTP/1.1" 302 0
[14/Nov/2025 10:30:47] "GET /employees/ HTTP/1.1" 200 8234
```

**HTTP Status Codes:**
- `200` = OK (request successful)
- `302` = Redirect (login success)
- `404` = Not Found
- `405` = Method Not Allowed (wrong HTTP method)
- `500` = Server Error

### **2. Check for Errors**
If you see errors in the terminal:
```
Error: [some error message]
Traceback (most recent call last):
  ...
```

1. **Read the error message carefully** - it tells you what went wrong
2. **Note the line number** - where the error occurred
3. **Check the traceback** - shows the sequence of function calls

### **3. Django System Check**
To check for configuration issues:
```bash
python manage.py check
```

Output should be:
```
System check identified no issues (0 silenced).
```

If there are issues, they will be listed.

### **4. Database Status**
Check if database migrations are applied:
```bash
python manage.py showmigrations
```

All migrations should show `[X]` (checked):
```
[X] 0001_initial
[X] 0002_alter_user_options
[X] 0003_alter_user_verbose_name_max_length
...
[X] 0016_replace_is_operator_with_employee_type
```

If any show `[ ]` (unchecked), run migrations:
```bash
python manage.py migrate
```

---

## Testing Pages

### **After Server Starts:**

1. **Login Page**
   - URL: `http://127.0.0.1:8000/accounts/login/`
   - Test username: `admin` (or any valid user)
   - You should see: Professional gradient login form

2. **Dashboard (after login)**
   - URL: `http://127.0.0.1:8000/`
   - Shows metrics, charts, quick actions

3. **Logout**
   - Click user menu (top right) → Sign Out
   - You should see: Success page with logout confirmation

4. **Employee List**
   - URL: `http://127.0.0.1:8000/employees/`
   - Shows list of all employees

---

## Common Issues & Solutions

### **Error: "Page not found" (404)**
- Check the URL is correct
- Ensure URL pattern exists in `urls.py`
- Server must be running

### **Error: "Method Not Allowed" (405)**
- Usually means POST/GET mismatch
- Check if form is using correct method
- ✅ **FIXED** for logout (now accepts GET and POST)

### **Error: "ModuleNotFoundError"**
- Make sure venv is activated
- Check if package is installed: `pip list`
- Install missing packages: `pip install [package-name]`

### **Error: "No such table" (database error)**
- Run migrations: `python manage.py migrate`
- Check if DB is created

### **Server won't start**
- Check if port 8000 is in use
- Use different port: `python manage.py runserver 8001`
- Check for syntax errors in code

---

## Terminal Commands Reference

```bash
# Activate environment
source venv/Scripts/activate              # Windows PowerShell/Git Bash
venv\Scripts\activate                     # Windows CMD

# Start server
python manage.py runserver                # Default (localhost:8000)
python manage.py runserver 0.0.0.0:8000  # Accessible from network
python manage.py runserver 8001           # Different port

# Database
python manage.py migrate                  # Apply migrations
python manage.py makemigrations          # Create new migrations
python manage.py showmigrations           # Show migration status

# Check
python manage.py check                    # System check
python manage.py test                     # Run tests

# Shell
python manage.py shell                    # Interactive Python shell

# Users
python manage.py createsuperuser          # Create admin user
python manage.py changepassword [user]   # Change user password

# Stop server
CTRL + C                                  # Stop running server
```

---

## Understanding Debug Messages

### **Request Log Format:**
```
[DATE TIME] "METHOD PATH HTTP_VERSION" STATUS_CODE SIZE
[14/Nov/2025 10:30:45] "GET / HTTP/1.1" 200 5234
```

- `METHOD`: GET, POST, PUT, DELETE, etc.
- `PATH`: The URL path accessed
- `STATUS_CODE`: Response code
- `SIZE`: Response size in bytes

### **Template Error:**
```
TemplateDoesNotExist at /path/
template.html
```
→ Template file not found in templates folder

### **View Error:**
```
ViewDoesNotExist: Could not import 'app.views.view_name'
```
→ View function/class doesn't exist or has wrong name

---

## Keeping Server Running

### **Option 1: Separate Terminal Windows**
1. Open Terminal 1: For server
2. Open Terminal 2: For other commands

### **Option 2: Background Process** (not recommended for development)
```bash
python manage.py runserver &
```

### **Option 3: Use IDE Terminal**
PyCharm, VS Code have built-in terminals where server keeps running.

---

## Testing the Logout Fix

1. **Start server**: `python manage.py runserver`
2. **Go to login**: `http://127.0.0.1:8000/accounts/login/`
3. **Login** with valid credentials
4. **Direct logout**: Visit `http://127.0.0.1:8000/accounts/logout/` directly
   - ✅ Should now work (previously gave 405 error)
   - ✅ Should show logout confirmation page
5. **Or click Sign Out** in user menu dropdown
   - Should also work

---

## Next Steps

After confirming the server works:
1. ✅ Test login/logout flow
2. ✅ Check dashboard loads
3. ✅ Try employee list
4. Begin implementing other sidebar features:
   - Analytics
   - Departments
   - Attendance
   - Reports
   - Tasks
   - Schedule
   - Payroll

Let me know if you encounter any issues!
