# Troubleshooting Guide

## Quick Checklist

### **Server Won't Start**
- [ ] Virtual environment activated? (`source venv/Scripts/activate`)
- [ ] Port 8000 available? (Try `python manage.py runserver 8001`)
- [ ] Python syntax errors? (Check terminal for errors)
- [ ] All dependencies installed? (`pip install -r requirements.txt`)

### **Page Shows 404 (Not Found)**
- [ ] URL spelling correct?
- [ ] URL exists in `floor_mgmt/urls.py` or `floor_app/hr/urls.py`?
- [ ] Server running?
- [ ] Page requires login? (Login first)

### **Page Shows 405 (Method Not Allowed)**
- [ ] ✅ **Logout now fixed** - should work
- [ ] Using correct HTTP method? (GET for links, POST for forms)
- [ ] Check view configuration

### **Database Errors ("no such table")**
```bash
python manage.py migrate
```

### **Template Not Found Error**
- [ ] Template file exists in `floor_app/templates/`?
- [ ] Template path correct in view?
- [ ] Subdirectories created? (e.g., `templates/registration/`)

### **Import Errors**
- [ ] Module/function actually exists?
- [ ] File in correct directory?
- [ ] Typo in import path?
- [ ] Package installed? (`pip list`)

---

## Logout Page - Fixed! ✅

### **What Was Wrong:**
- Django's LogoutView only accepts POST requests by default
- Direct URL access (`GET` request) gave HTTP 405 error

### **What's Fixed:**
- CustomLogoutView now accepts both GET and POST
- Direct logout link now works: `http://127.0.0.1:8000/accounts/logout/`
- User menu logout still works

### **How to Test:**
1. Activate venv and start server
2. Login with valid credentials
3. Try both methods:
   - **Method 1**: Click "Sign Out" in user menu (top right)
   - **Method 2**: Visit URL directly: `http://127.0.0.1:8000/accounts/logout/`
4. Both should show logout confirmation page

---

## Reading Server Logs

### **Normal Request:**
```
[14/Nov/2025 10:30:45] "GET / HTTP/1.1" 200 5234
                        ↑                    ↑    ↑
                        Method/Path          Status Size
                        Success response (200)
```

### **Redirect (Login Success):**
```
[14/Nov/2025 10:30:46] "POST /accounts/login/ HTTP/1.1" 302 0
                                                          ↑
                                                          302 = Redirect
                                                          Size 0 = No body
```

### **Not Found Error:**
```
[14/Nov/2025 10:30:47] "GET /nonexistent/ HTTP/1.1" 404 2485
                                                       ↑
                                                       404 = Not Found
```

### **Method Error (Before Fix):**
```
[14/Nov/2025 10:30:48] "GET /accounts/logout/ HTTP/1.1" 405 0
                                                         ↑
                                                         405 = Method Not Allowed
                                                         Now FIXED ✅
```

### **Server Error:**
```
[14/Nov/2025 10:30:49] "GET /path/ HTTP/1.1" 500 2123
                                               ↑
                                               500 = Server Error
                                               Check terminal for traceback
```

---

## Common Error Messages & Fixes

### **Error: "TemplateDoesNotExist"**
```
TemplateDoesNotExist at /accounts/login/
registration/login.html
```
**Fix:**
- Check if file exists: `floor_app/templates/registration/login.html`
- Check TEMPLATES setting in `settings.py`
- Restart server after adding template

### **Error: "ViewDoesNotExist"**
```
ViewDoesNotExist: Could not import 'floor_app.views.nonexistent'
```
**Fix:**
- Check function/class name exists in `floor_app/views.py`
- Check spelling in `urls.py`
- Restart server

### **Error: "ModuleNotFoundError"**
```
ModuleNotFoundError: No module named 'some_package'
```
**Fix:**
```bash
pip install some_package
```

### **Error: "No such table"**
```
OperationalError: no such table: floor_app_hrremployee
```
**Fix:**
```bash
python manage.py migrate
```

### **Error: "CSRF token missing"**
```
Forbidden (403)
CSRF token missing or incorrect.
```
**Fix:**
- Add `{% csrf_token %}` in forms
- Form must use `method="post"`

---

## Checking Everything Works

### **1. Basic System Check:**
```bash
python manage.py check
```
Should output:
```
System check identified no issues (0 silenced).
```

### **2. Database Check:**
```bash
python manage.py migrate
```
Should show:
```
Operations to perform:
  Apply all migrations: admin, auth, ...
Running migrations:
  ...
```

### **3. Start Server:**
```bash
python manage.py runserver
```
Should show:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### **4. Test Pages:**
- Login page: `http://127.0.0.1:8000/accounts/login/` → 200 OK
- Dashboard: `http://127.0.0.1:8000/` → 200 OK (after login)
- Logout: `http://127.0.0.1:8000/accounts/logout/` → Shows confirmation ✅

---

## Server Status Indicators

### **🟢 Server Running Normally:**
- Terminal shows: `Starting development server at http://127.0.0.1:8000/`
- Terminal shows HTTP requests: `[TIME] "GET /path/ HTTP/1.1" 200 SIZE`
- Pages load without error

### **🟡 Server Has Issues:**
- Terminal shows error messages but didn't crash
- Pages show error pages (404, 500, etc.)
- Check terminal for details

### **🔴 Server Crashed:**
- Terminal stopped updating
- "Quit the server with CONTROL-C" disappeared
- Error traceback visible in terminal
- Press CTRL+C and try `python manage.py runserver` again

---

## Restarting Server

If you change Python code:
1. **Save the file**
2. **Server restarts automatically** (if `DEBUG=True`)
3. **Refresh page** in browser

If automatic restart doesn't work:
1. **Press CTRL+C** in terminal
2. **Run again**: `python manage.py runserver`

---

## Need More Help?

If you encounter an error:
1. **Copy the exact error message** from terminal
2. **Note the URL** you were accessing
3. **Save the traceback** (the full error details)
4. **Share all of this** and I can help debug

Example error report:
```
URL: http://127.0.0.1:8000/employees/
Method: GET
Error in terminal:
[14/Nov/2025 10:30:45] "GET /employees/ HTTP/1.1" 500 2123
Traceback (most recent call last):
  File "...", line X, in ...
    NameError: name 'employee_list' is not defined
```

This helps identify the exact problem!
