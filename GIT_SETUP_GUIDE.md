# Git Repository Setup Guide

This guide walks you through creating a Git repository for your application and pushing it to GitHub/GitLab.

## Step 1: Check if Git is Installed

**On Windows (PowerShell):**
```powershell
git --version
```

If Git is not installed, download it from: https://git-scm.com/download/win

## Step 2: Configure Git (First Time Setup)

**Before you can commit, Git needs to know who you are!**

Configure your Git identity (use your GitHub email and name):

```powershell
# Set your name (use your real name or GitHub username)
git config --global user.name "Your Name"

# Set your email (use your GitHub email)
git config --global user.email "your.email@example.com"
```

**Example:**
```powershell
git config --global user.name "kcaiagent"
git config --global user.email "your-github-email@example.com"
```

**Verify your settings:**
```powershell
git config --global --list
```

**Note**: The `--global` flag sets this for all Git repositories on your computer. If you want to set it only for this project, remove `--global`.

## Step 3: Initialize Git Repository (If Not Already Done)

Navigate to your project directory:

```powershell
cd "C:\Users\kyoto\OneDrive\Desktop\AI EMAIL WEBAPP"
```

Check if Git is already initialized:
```powershell
git status
```

If you see "not a git repository", initialize it:
```powershell
git init
```

## Step 4: Verify .gitignore File

Your project already has a `.gitignore` file. Make sure it includes:

- Environment files (`.env`, `.env.local`)
- Python cache files (`__pycache__/`, `*.pyc`)
- Database files (`*.db`, `*.sqlite`)
- IDE files (`.vscode/`, `.idea/`)
- Virtual environments (`venv/`, `env/`)
- Generated files (`pdf_quotes/*.pdf`, `uploads/`)

## Step 5: Stage and Commit Your Files

**Add all files to Git:**
```powershell
git add .
```

**Check what will be committed:**
```powershell
git status
```

**Create your first commit:**
```powershell
git commit -m "Initial commit: Email Quote System API"
```

## Step 6: Create Repository on GitHub

### Option A: Using GitHub Website

1. **Go to GitHub**
   - Visit [https://github.com](https://github.com)
   - Sign in or create an account

2. **Create New Repository**
   - Click the **"+"** icon in top right → **"New repository"**
   - **Repository name**: `email-quote-system` (or your choice)
   - **Description**: "AI-powered email-to-quote system"
   - **Visibility**: 
     - Choose **Private** (recommended for production apps)
     - Or **Public** (if you want it open source)
   - **DO NOT** check "Initialize with README" (you already have files)
   - **DO NOT** add .gitignore or license (you already have them)
   - Click **"Create repository"**

3. **Copy the repository URL**
   - You'll see a page with setup instructions
   - Copy the HTTPS URL (e.g., `https://github.com/yourusername/email-quote-system.git`)
   - Or SSH URL if you have SSH keys set up

### Option B: Using GitHub CLI (If Installed)

```powershell
# Install GitHub CLI first: https://cli.github.com/
gh auth login
gh repo create email-quote-system --private --source=. --remote=origin --push
```

## Step 7: Connect Local Repository to GitHub

**Add GitHub as remote:**
```powershell
# Replace with your actual repository URL
git remote add origin https://github.com/YOUR_USERNAME/email-quote-system.git
```

**Verify remote was added:**
```powershell
git remote -v
```

## Step 8: Push Your Code to GitHub

**Push to GitHub:**
```powershell
git branch -M main
git push -u origin main
```

**If prompted for credentials:**
- **Username**: Your GitHub username
- **Password**: Use a **Personal Access Token** (not your GitHub password)
  - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate new token with `repo` scope
  - Copy and use as password

## Step 9: Verify Push Was Successful

1. Go to your GitHub repository page
2. You should see all your files
3. Check that sensitive files (`.env`, `*.db`) are NOT visible

## Step 10: Clone on Your Hetzner Server

Now you can clone the repository on your server:

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/email-quote-system.git email-quote-api
cd email-quote-api
```

**For private repositories**, you'll need to authenticate:
- Use a Personal Access Token as the password
- Or set up SSH keys on the server

## Common Git Commands

### Daily Workflow

```powershell
# Check status
git status

# See what changed
git diff

# Add specific files
git add filename.py

# Add all changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push

# Pull latest changes
git pull
```

### Branching (Optional)

```powershell
# Create new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Merge branch
git checkout main
git merge feature-name

# Delete branch
git branch -d feature-name
```

### Updating After Code Changes

```powershell
# After making changes locally
git add .
git commit -m "Description of your changes"
git push

# On server, pull latest changes
cd /opt/email-quote-api
git pull
```

## Security Best Practices

1. **Never commit sensitive files:**
   - `.env` files
   - API keys
   - Passwords
   - Database files

2. **Use environment variables:**
   - Store secrets in `.env` (which is in `.gitignore`)
   - Create `.env.example` as a template:
     ```powershell
     # Copy this file to .env and fill in your values
     cp .env.example .env
     ```

3. **Review before pushing:**
   ```powershell
   git status
   git diff
   ```

## Troubleshooting

### "Author identity unknown" Error

This error means Git doesn't know who you are. You need to configure your name and email first.

**Solution: Configure Git Identity**

```powershell
# Set your name (use your GitHub username or real name)
git config --global user.name "Your Name"

# Set your email (use your GitHub email)
git config --global user.email "your.email@example.com"

# Verify it worked
git config --global --list
```

**Then try committing again:**
```powershell
git commit -m "Initial commit: Email Quote System API"
```

### "src refspec main does not match any" Error

This error means you **haven't created any commits yet**. Git needs at least one commit before you can push.

**Solution: Create your first commit**

```powershell
# First, make sure Git knows who you are (see above)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Check current status
git status

# Add all files
git add .

# Create your first commit
git commit -m "Initial commit: Email Quote System API"

# Check what branch you're on
git branch

# If you're on 'master' instead of 'main', rename it:
git branch -M main

# Now push
git push -u origin main
```

**If you see "nothing to commit":**
- Check if files are already committed: `git log`
- Check if files are ignored: `git status` (should show untracked files)
- Make sure you're in the right directory

### "failed to push some refs" Error

This is the **most common error** when pushing for the first time. It usually means the remote repository has commits that your local repository doesn't have.

**Solution 1: Pull and Merge (Recommended)**

```powershell
# Fetch the remote changes
git fetch origin

# Merge remote changes with your local changes
git pull origin main --allow-unrelated-histories

# Resolve any conflicts if they occur, then:
git add .
git commit -m "Merge remote and local changes"

# Now push
git push -u origin main
```

**Solution 2: Force Push (Use with Caution - Only for New Repos)**

⚠️ **Only use this if you're sure the remote repository is empty or you don't need its contents:**

```powershell
# Force push (overwrites remote)
git push -u origin main --force
```

**Solution 3: If You Initialized GitHub Repo with README**

If you accidentally checked "Initialize with README" when creating the repo:

```powershell
# Pull the README from remote
git pull origin main --allow-unrelated-histories

# If there are conflicts, resolve them, then:
git add .
git commit -m "Merge with remote README"
git push -u origin main
```

**Solution 4: Start Fresh (Nuclear Option)**

If nothing else works and you don't care about the remote content:

```powershell
# Remove the remote
git remote remove origin

# Add it back
git remote add origin https://github.com/YOUR_USERNAME/email-quote-system.git

# Force push
git push -u origin main --force
```

### "Repository not found" error
- Check repository URL is correct
- Verify you have access (for private repos)
- Check authentication (use Personal Access Token)
- Make sure the repository exists on GitHub

### "Permission denied" error
- Set up SSH keys for GitHub
- Or use HTTPS with Personal Access Token
- Make sure your Personal Access Token has `repo` scope

### "Authentication failed" error
- Use a Personal Access Token (not your GitHub password)
- Generate new token: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- Make sure token has `repo` scope

### Large files won't push
- Check `.gitignore` includes large files
- Use Git LFS for large files if needed
- Remove large files from Git history if already committed:
  ```powershell
  git rm --cached large-file.pdf
  git commit -m "Remove large file"
  git push
  ```

### Undo last commit (before pushing)
```powershell
git reset --soft HEAD~1
```

### Undo last commit (after pushing - be careful!)
```powershell
git revert HEAD
git push
```

## Next Steps

After setting up Git:
1. ✅ Push your code to GitHub
2. ✅ Clone on Hetzner server (see Deployment Guide Step 4)
3. ✅ Continue with Docker deployment

## Alternative: Use GitLab or Bitbucket

The process is similar:
- **GitLab**: https://gitlab.com
- **Bitbucket**: https://bitbucket.org

Just replace `github.com` with `gitlab.com` or `bitbucket.org` in the URLs.

