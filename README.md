# 🌩️ cf-alias

Command-line Cloudflare email aliases. Because your primary inbox deserves peace, quiet, and zero unwanted newsletters.

A lightweight Python CLI tool to generate and manage Cloudflare Email Routing aliases on the fly, directly from your terminal.

---

## ✨ Features

* **Quick Create:** Generate a new email alias in seconds — no dashboard required.
* **Spam Prevention:** Ditch the catch-all. Use explicit aliases to block spam at the network edge.
* **Simple Config:** Securely store your Cloudflare credentials and default forwarding address locally.

---

## 📋 Prerequisites

Before you begin, you will need:
1. A domain with Cloudflare Email Routing enabled.
2. A Cloudflare API Token with **Email Routing: Edit** permissions.
3. Your domain's **Zone ID** (found on the right-hand sidebar of your Cloudflare dashboard overview).

---

## 🚀 Installation & Setup

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/cf-alias.git
cd cf-alias
```

**2. Install dependencies**

**Option A — venv (standard Python):**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

**Option B — uv (recommended):**

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

**3. Configure your environment**

Copy the provided `.env.example` template to create your own `.env` file:
```bash
cp .env.example .env
```

Then, open the .env file and replace the placeholder values with your actual Cloudflare credentials.


---

## 💻 Usage
Create a new alias:
This creates a new alias rule — `github@yourdomain.com` — forwarding to your default destination address.

```bash
python cf-alias.py create github
```

### View help

View all available commands and options.

```bash
python cf-alias.py --help
```
