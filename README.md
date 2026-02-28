# Instagram Followees Scraper

This tool lets you extract the list of accounts that any Instagram user is **following**, along with details like their name, bio, number of followers, posts, email (if listed in bio), and more. The data gets saved as a spreadsheet (`.csv` file) that you can open in Excel or Google Sheets.

---

## What You Need Before Starting

- A computer running **Windows**, **Mac**, or **Linux**
- An **Instagram account** (the tool will log in through it)
- **Google Chrome** browser installed
- An internet connection

---

## Step-by-Step Setup

---

### On Windows

#### 1. Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click the big yellow **"Download Python"** button
3. Run the downloaded file
4. **IMPORTANT:** On the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install
5. Click **Install Now** and wait for it to finish

To verify it worked, open the **Start Menu**, search for **"Command Prompt"**, open it, and type:
```
python --version
```
You should see something like `Python 3.x.x`

#### 2. Install Google Chrome

If you don't already have Chrome, download it from [https://www.google.com/chrome/](https://www.google.com/chrome/) and install it normally.

#### 3. Download This Project

If you received this as a ZIP file, extract it to a location you can easily find, like your Desktop.

If you have Git installed, you can also run:
```
git clone https://github.com/imajij/instaScrapper.git
```

#### 4. Open the Project Folder in Command Prompt

1. Open **Command Prompt** (search for it in the Start Menu)
2. Navigate to the project folder. For example, if it's on your Desktop:
```
cd Desktop\instaScrapper
```

#### 5. Create a Virtual Environment

A virtual environment keeps this project's dependencies separate from other Python programs. Run:
```
python -m venv .venv
```

#### 6. Activate the Virtual Environment

```
.venv\Scripts\activate
```

You will see `(.venv)` appear at the start of your command line — this means it's active.

#### 7. Install Required Packages

```
pip install selenium webdriver-manager pandas
```

Wait for all packages to finish downloading and installing.

#### 8. Configure Your Credentials

Open the file `scrapper.py` in any text editor (Notepad works fine):

1. Find these three lines near the top of the file (around line 37):
   ```python
   INSTAGRAM_USERNAME = "your_username"
   INSTAGRAM_PASSWORD = "your_passwordd"
   TARGET_ACCOUNT = "ashneer.grover"
   ```
2. Replace `your_username` with your Instagram username
3. Replace `your_passwordd` with your Instagram password
4. Replace `ashneer.grover` with the Instagram username of the account whose following list you want to scrape

Save the file.

#### 9. Run the Scraper

Make sure your virtual environment is still active (you see `(.venv)` at the start), then run:
```
python scrapper.py
```

A Chrome browser window will open automatically. The tool will log in and start collecting data. **Do not close the Chrome window** while it is running.

You may need to scroll occasionally if the window gets stuck while fetching all followies .

---

### On Mac

#### 1. Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click the big yellow **"Download Python"** button (make sure it says macOS)
3. Open the downloaded `.pkg` file and follow the installation steps
4. Once installed, open the **Terminal** app (you can find it in Applications → Utilities → Terminal, or search for it with Spotlight using `Cmd + Space`)

Verify the installation by typing:
```
python3 --version
```
You should see something like `Python 3.x.x`

#### 2. Install Google Chrome

If you don't already have Chrome, download it from [https://www.google.com/chrome/](https://www.google.com/chrome/) and install it normally.

#### 3. Download This Project

If you received this as a ZIP file, extract it somewhere easy to find, like your Desktop.

Or, if you have Git, open Terminal and run:
```
git clone https://github.com/imajij/instaScrapper.git
```

#### 4. Open the Project Folder in Terminal

In the Terminal, navigate to the project folder. For example, if it's on your Desktop:
```
cd ~/Desktop/instaScrapper
```

#### 5. Create a Virtual Environment

```
python3 -m venv .venv
```

#### 6. Activate the Virtual Environment

```
source .venv/bin/activate
```

You will see `(.venv)` appear at the start of your terminal prompt — this means it's active.

#### 7. Install Required Packages

```
pip install selenium webdriver-manager pandas
```

Wait for all packages to finish downloading and installing.

#### 8. Configure Your Credentials

Open `scrapper.py` in a text editor. You can use TextEdit, or any code editor you have.

Find these lines near the top of the file:
```python
INSTAGRAM_USERNAME = "your_username"
INSTAGRAM_PASSWORD = "your_passwordd"
TARGET_ACCOUNT = "ashneer.grover"
```

- Replace `your_username` with your Instagram username
- Replace `your_passwordd` with your Instagram password
- Replace `ashneer.grover` with the Instagram username of the account whose following list you want to scrape

Save and close the file.

#### 9. Run the Scraper

Make sure you're still in the project folder and your virtual environment is active, then run:
```
python scrapper.py
```

A Chrome browser window will open automatically. The tool will log in and start collecting data. **Do not close the Chrome window** while it is running.

---

### On Linux

#### 1. Install Python

Most Linux distributions come with Python pre-installed. Check by opening a **Terminal** and typing:
```
python3 --version
```

If it's not installed, run the following based on your distribution:

**Ubuntu / Debian:**
```
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

**Fedora:**
```
sudo dnf install python3 python3-pip -y
```

**Arch Linux:**
```
sudo pacman -S python python-pip
```

#### 2. Install Google Chrome

**Ubuntu / Debian:**
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y
```

**Fedora:**
```
sudo dnf install fedora-workstation-repositories -y
sudo dnf config-manager --set-enabled google-chrome
sudo dnf install google-chrome-stable -y
```

**Arch Linux:**
```
yay -S google-chrome
```

#### 3. Download This Project

If you received a ZIP file, extract it. Or clone it with Git:
```
git clone https://github.com/imajij/instaScrapper.git
cd instaScrapper
```

If you already have the folder, navigate to it:
```
cd ~/Desktop/instaScrapper
```

#### 4. Create a Virtual Environment

```
python3 -m venv .venv
```

#### 5. Activate the Virtual Environment

```
source .venv/bin/activate
```

You will see `(.venv)` at the start of your terminal — this means it's active.

#### 6. Install Required Packages

```
pip install selenium webdriver-manager pandas
```

#### 7. Configure Your Credentials

Open `scrapper.py` in a text editor:
```
nano scrapper.py
```

Find these lines near the top:
```python
INSTAGRAM_USERNAME = "your_username"
INSTAGRAM_PASSWORD = "your_passwordd"
TARGET_ACCOUNT = "ashneer.grover"
```

- Replace `your_username` with your Instagram username
- Replace `your_passwordd` with your Instagram password
- Replace `ashneer.grover` with the Instagram username of the account whose following list you want to scrape

Save the file: press `Ctrl + X`, then `Y`, then `Enter`.

#### 8. Run the Scraper

```
python scrapper.py
```

Or use the provided helper script:
```
bash run.sh
```

A Chrome window will open. The tool will log in and begin scraping. **Do not close the Chrome window** while it is running.

---

## Where Is My Data Saved?

Once the scraper finishes, it saves a file called:
```
<target_account>_followees_detailed.csv
```

For example, if you scraped `ashneer.grover`, the file will be named `ashneer.grover_followees_detailed.csv`.

This file is saved in the same folder as `scrapper.py`. You can open it directly with:
- **Microsoft Excel**
- **Google Sheets** (upload it at [sheets.google.com](https://sheets.google.com))
- **LibreOffice Calc** (free, available on all platforms)

---

## Resuming After an Interruption

If the scraper is interrupted (closed by accident, internet cut, etc.), it automatically saves its progress to a checkpoint file named `<target_account>_checkpoint.json`. The next time you run `python scrapper.py`, it will pick up from where it left off.

---

## Common Problems & Fixes

| Problem | Fix |
|---|---|
| `python` is not recognized | Use `python3` instead of `python` on Mac/Linux |
| Chrome doesn't open | Make sure Google Chrome is installed |
| Login failed | Double-check your username and password in `scrapper.py` |
| Script stops mid-way | Re-run it — the checkpoint will resume from where it stopped |
| `ModuleNotFoundError` | Make sure your virtual environment is active and you ran `pip install ...` |
| Instagram asks for a verification code | Complete the verification manually in the opened Chrome window |
| **(macOS) Chrome opens but the script can't type into fields / crashes immediately** | macOS Gatekeeper quarantines the auto-downloaded `chromedriver`. Run this once in Terminal, then retry: `xattr -d com.apple.quarantine $(python -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())")` |
| **(macOS) "chromedriver cannot be opened because it is from an unidentified developer"** | Same fix as above — the Gatekeeper quarantine attribute needs to be removed from the downloaded driver binary. |

---

## Optional Settings

Inside `scrapper.py`, you can also adjust these settings near the top of the file:

| Setting | What it does | Default |
|---|---|---|
| `MAX_FOLLOWEES_TO_COLLECT` | Limit how many accounts to collect (useful for testing). Set to a number like `50`, or leave as `None` to collect all | `None` |
| `HEADLESS` | Set to `True` to run Chrome invisibly in the background | `False` |
| `BATCH_SIZE` | How many profiles to process per batch | `25` |

---

## Important Notes

- This tool uses your own Instagram account to scrape, so use it responsibly and avoid running it too frequently to prevent your account from being flagged.
- Instagram may occasionally ask for a CAPTCHA or verification — if that happens, complete it manually in the Chrome window that opens.
- The tool adds random delays between actions to mimic human behavior and reduce the risk of being detected.
