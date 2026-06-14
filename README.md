# WebSpy 🕵️

A simple, beautiful command-line tool to scrape webpages — extract clean readable text, list categorized hyperlinks, and export everything to clean files.

---

## 📁 File Structure

```
webspy/
├── webspy.py          # Main CLI application
├── requirements.txt   # Python dependencies
├── README.md          # This file
├── .gitignore
└── exports/           # Auto-created folder for --export output
    └── .gitkeep
```

---

## ⚙️ Requirements

- **Python 3.13.5** (tested and supported as of v1.0.0)
- pip

### Dependencies (`requirements.txt`)

```
typer==0.12.5
requests==2.32.3
beautifulsoup4==4.12.3
rich==13.9.4
lxml==5.3.0
```

---

## 🚀 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/webspy.git
   cd webspy
   ```

2. **(Recommended) Create a virtual environment**
   ```bash
   python -m venv venv

   # Activate it:
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the tool**
   ```bash
   python webspy.py --help
   ```

---

## 📖 Commands

### 1. `dump` — Extract main readable text from a page

```bash
python webspy.py dump <URL>
```

Fetches the page, strips out scripts, navs, headers, footers, ads, and prints only the main readable content (title + body text) to the terminal in a clean format.

**With export (saves as Markdown):**
```bash
python webspy.py dump <URL> --export
python webspy.py dump <URL> -e
```
Saves to `exports/<domain>_<path>_dump.md`

---

### 2. `links` — Extract and categorize hyperlinks

```bash
python webspy.py links <URL>
```

Fetches the page and displays a color-coded Rich table:
- 🟢 **Internal Links** (same domain)
- 🟣 **External Links** (different domain)

Binary files (images, audio, video, documents) are shown with a label like `[IMAGE] photo.jpg` or `[VIDEO] clip.mp4` instead of the raw link text.

**With export (saves as plain text):**
```bash
python webspy.py links <URL> --export
python webspy.py links <URL> -e
```
Saves to `exports/<domain>_<path>_links.txt`

---

### 3. Help commands

```bash
python webspy.py --help          # Show all commands
python webspy.py dump --help      # Show options for 'dump'
python webspy.py links --help     # Show options for 'links'
```

---

## 🧪 Example Usage

```bash
# Print main article text from a blog
python webspy.py dump https://example.com/blog/post-1

# Save the article as a markdown file
python webspy.py dump https://example.com/blog/post-1 -e

# View all links on a homepage, color-coded
python webspy.py links https://example.com

# Export the link list to a text file
python webspy.py links https://example.com -e
```

---

## 🛣️ Roadmap / Notes

- **v1.0.0** — Initial release. Supports `dump` and `links` with `--export` flag. Built and tested on **Python 3.13.5**.
- Graceful handling of connection errors, timeouts, and HTTP errors.
- Future versions may include a "named bookmarks" table feature for quick re-fetching of saved links by name.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

