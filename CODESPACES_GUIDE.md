# 🌐 GitHub Codespaces Guide - Run Django in Browser

## What is GitHub Codespaces?

**GitHub Codespaces** is a **cloud development environment** that runs directly in your browser. No installation needed!

Think of it as:
- 🖥️ **VS Code in your browser**
- 🐳 **Docker containers in the cloud**
- 🌐 **Live website preview** with real URL
- ⚡ **Instant setup** - ready in 2 minutes

### Perfect For:
✅ Reviewing HTML pages live
✅ Testing the application
✅ No local installation needed
✅ Works on any computer with browser
✅ Same environment for everyone

---

## 🚀 Quick Start - 3 Steps

### Step 1: Open in Codespaces

Go to your GitHub repository and click:

```
Code button (green) → Codespaces tab → Create codespace on <branch>
```

**Or use direct link:**
```
https://github.com/<your-username>/Floor-Management-System/codespaces
```

**Select branch:** `claude/floor-system-health-check-01THJSxKiE5nspKXgwWdDiA5`

### Step 2: Wait for Setup (2-3 minutes)

Codespaces will automatically:
- ✅ Create a Linux VM
- ✅ Install Python & Docker
- ✅ Start PostgreSQL
- ✅ Run migrations
- ✅ Load test data
- ✅ Start Django server

**Watch the terminal** for setup progress.

### Step 3: Open the Web Application

When setup completes, you'll see:

**Option A: Notification Popup**
- Click "Open in Browser" when popup appears

**Option B: Ports Tab**
1. Click "PORTS" tab at bottom of VS Code
2. Find port **8000** (Django Web Server)
3. Click the globe icon 🌐 or right-click → "Open in Browser"

**Option C: Terminal**
- Look for the forwarded URL in terminal output
- URL format: `https://<codespace-name>-8000.app.github.dev`

---

## 🎯 What You'll See

Once opened, you'll have:

- **Live Django Application** running in browser
- **Full admin panel** at `/admin/`
- **Health check** at `/api/health/`
- **All HTML pages** accessible and working

You can now:
- ✅ Click through all pages
- ✅ Test forms and buttons
- ✅ Review layouts and designs
- ✅ Check for errors (F12 for console)
- ✅ Test workflows end-to-end

---

## 🔧 Using the Codespace

### Access Different URLs

```
Main App:      https://<codespace-name>-8000.app.github.dev
Admin Panel:   https://<codespace-name>-8000.app.github.dev/admin/
Health Check:  https://<codespace-name>-8000.app.github.dev/api/health/
API Docs:      https://<codespace-name>-8000.app.github.dev/api/
```

### Useful Terminal Commands

```bash
# View logs
docker-compose logs -f web

# Create superuser (admin account)
docker-compose exec web python manage.py createsuperuser

# Django shell
docker-compose exec web python manage.py shell

# Check templates
docker-compose exec web python scripts/check_templates.py

# Run tests
docker-compose exec web python manage.py test

# Restart server
docker-compose restart web

# Stop everything
docker-compose down
```

### Edit Code Live

1. Edit any file in the left sidebar
2. Save (Ctrl+S / Cmd+S)
3. Changes apply automatically
4. Refresh browser to see updates

---

## 🐛 Troubleshooting

### Issue 1: "Port 8000 Not Found"

**Solution:**
```bash
# Check if containers are running
docker-compose ps

# Start containers if not running
docker-compose up -d

# Wait 30 seconds, then check ports tab again
```

### Issue 2: "Database Connection Error"

**Solution:**
```bash
# Restart database
docker-compose restart db

# Wait 10 seconds
sleep 10

# Restart web server
docker-compose restart web
```

### Issue 3: "Permission Denied"

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run setup again
bash scripts/codespace_setup.sh
```

### Issue 4: "Page Not Loading"

**Solution:**
```bash
# Check if Django is running
docker-compose logs web

# Look for errors in log

# Try accessing health check first
curl http://localhost:8000/api/health/

# If health check works, issue is with port forwarding
# Click "Ports" tab and make port 8000 "Public"
```

---

## 💰 Cost & Limits

### Free Tier (Personal Accounts)
- ✅ **60 hours/month** free
- ✅ **15 GB storage** per codespace
- ✅ **2 core machine** (default)

### Tips to Save Hours:
- ⏸️ **Stop codespace** when not using (automatic after 30 min idle)
- 🗑️ **Delete** when done reviewing
- ⏱️ **Use efficiently** - complete reviews in one session

### Check Your Usage:
```
GitHub Settings → Billing → Codespaces
```

---

## 📊 Comparing Options

| Feature | GitHub Codespaces | Local Docker | Local Python |
|---------|-------------------|--------------|--------------|
| **Setup Time** | 2-3 minutes | 5-10 minutes | 30+ minutes |
| **Installation** | None | Docker Desktop | Python, PostgreSQL, etc. |
| **Cost** | Free (60hrs) | Free | Free |
| **Accessibility** | Any browser | Your machine only | Your machine only |
| **Team Sharing** | Easy (share link) | Share code only | Share code only |
| **Performance** | Good | Best | Good |
| **Internet Required** | Yes | No | No |

---

## 🎯 Best For Each Scenario

### Use **GitHub Codespaces** When:
✅ Quick review needed
✅ No local setup available
✅ Need to share live preview
✅ Testing on clean environment
✅ Team collaboration

### Use **Local Docker** When:
✅ Extended development work
✅ Offline work needed
✅ Better performance required
✅ Already have Docker installed
✅ Want to save Codespace hours

### Use **Local Python** When:
✅ Docker not available
✅ Learning Django
✅ Debugging deep issues
✅ Custom environment needed

---

## 🔐 Security Notes

### Codespaces are Secure:
✅ Isolated environment per user
✅ Private by default
✅ Automatic HTTPS
✅ GitHub authentication required

### Best Practices:
- ⚠️ Don't commit sensitive data
- ⚠️ Use environment variables for secrets
- ⚠️ Make ports "Private" (default)
- ⚠️ Delete codespaces when done
- ⚠️ Review code before sharing preview

### Port Visibility:
- **Private** (default) - Only you can access
- **Public** - Anyone with URL can access
- **Organization** - Your org members can access

**For reviewing:** Keep ports **Private** unless need to share.

---

## 📝 Step-by-Step Review Workflow

### Complete Review Process:

**1. Start Codespace** (2 minutes)
```
GitHub → Code → Codespaces → Create
```

**2. Wait for Setup** (2 minutes)
- Watch terminal for completion
- Look for "✅ Setup complete!"

**3. Open Application** (1 minute)
```
Ports tab → Port 8000 → Open in Browser
```

**4. Create Admin Account** (1 minute)
```bash
docker-compose exec web python manage.py createsuperuser
# Enter: username, email, password
```

**5. Review Pages** (15-30 minutes)
- ✅ Homepage
- ✅ Login/logout
- ✅ Admin panel
- ✅ List views (employees, inventory, production)
- ✅ Detail views
- ✅ Forms (create, edit, delete)
- ✅ Search functionality
- ✅ Reports
- ✅ Navigation menus

**6. Check for Issues** (10 minutes)
- Open browser console (F12)
- Look for red errors
- Test forms submit correctly
- Check responsive design (resize browser)
- Verify images load
- Test all buttons

**7. Check Template Issues** (5 minutes)
```bash
docker-compose exec web python scripts/check_templates.py
```

**8. Fix Issues Found** (as needed)
```bash
# Automated fixes
docker-compose exec web python scripts/fix_templates.py --apply

# Manual fixes - edit files in VS Code
```

**9. Test Again** (5 minutes)
```bash
# Restart server
docker-compose restart web

# Run tests
docker-compose exec web python manage.py test

# Review again in browser
```

**10. Commit & Stop** (2 minutes)
```bash
# Commit changes if any
git add .
git commit -m "fix: resolve template issues found in review"
git push

# Stop codespace (or it auto-stops after 30 min)
# Go to GitHub → Codespaces → Stop
```

**Total Time:** ~40-60 minutes for complete review

---

## 🎓 Advanced Tips

### Share Live Preview with Team

```bash
# 1. Make port public
Ports tab → Right-click port 8000 → Port Visibility → Public

# 2. Share the URL
Copy URL from Ports tab
Send to team members

# 3. They can view (read-only access)
```

### Custom Codespace Configuration

Edit `.devcontainer/devcontainer.json`:

```json
{
  "forwardPorts": [8000, 5433],
  "postCreateCommand": "pip install -r requirements.txt",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "batisteo.vscode-django"
      ]
    }
  }
}
```

### Use Prebuilds (Faster Startup)

```
Repository Settings → Codespaces → Set up prebuild

This pre-builds containers, reducing startup from 3min to 30sec
```

### Connect Local VS Code

```bash
# Install GitHub Codespaces extension in VS Code desktop

# Connect to codespace
Command Palette → Codespaces: Connect to Codespace

# Now work in desktop VS Code with cloud backend
```

---

## ❓ FAQ

**Q: Do I need to install anything?**
A: No! Just a web browser.

**Q: Can multiple people use same codespace?**
A: No, but you can share the preview URL.

**Q: What happens to my data?**
A: Data is in the codespace. Commit to Git to save permanently.

**Q: Can I use this for production?**
A: No, use for development/review only.

**Q: How do I stop charges?**
A: Stop or delete codespace when done. Auto-stops after 30 min.

**Q: Is it faster than local?**
A: Similar performance. Depends on internet speed.

**Q: Can I customize the environment?**
A: Yes, edit `.devcontainer/devcontainer.json`

**Q: What if I run out of free hours?**
A: Switch to local Docker, or pay $0.18/hour for additional time.

---

## ✅ Review Checklist

Use this when reviewing in Codespaces:

### Setup ✓
- [ ] Codespace created successfully
- [ ] Django server started (port 8000)
- [ ] Database connected
- [ ] Test data loaded
- [ ] Admin account created

### Pages ✓
- [ ] Homepage loads
- [ ] Login/logout works
- [ ] Admin panel accessible
- [ ] All list views load
- [ ] All detail views load
- [ ] Forms work (create/edit/delete)
- [ ] Search functionality works
- [ ] Navigation menus work

### Visual ✓
- [ ] No broken layouts
- [ ] Images load correctly
- [ ] CSS/styling works
- [ ] Responsive on mobile
- [ ] Tables display properly
- [ ] Forms render correctly

### Console ✓
- [ ] No JavaScript errors (F12)
- [ ] No 404 errors
- [ ] No CSRF errors
- [ ] No template errors

### Template Check ✓
- [ ] Ran template checker
- [ ] Reviewed issues found
- [ ] Applied automated fixes
- [ ] Fixed remaining issues

### Testing ✓
- [ ] Health check passes
- [ ] Automated tests pass
- [ ] Manual smoke test complete

---

## 🎉 Success!

You now have a **live Django application** running in your **browser** without any local installation!

**Next Steps:**
1. ✅ Review all HTML pages
2. ✅ Fix any issues found
3. ✅ Commit changes
4. ✅ Merge to main branch
5. ✅ Deploy to production

**Need Help?**
- Check terminal output for errors
- Review Docker logs: `docker-compose logs`
- See QUICK_START_GUIDE.md
- See DOCKER_SETUP.md

---

**Happy reviewing! 🚀**

*GitHub Codespaces makes it incredibly easy to review and test the Floor Management System without any local setup!*
