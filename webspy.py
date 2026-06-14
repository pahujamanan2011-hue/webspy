#!/usr/bin/env python3
"""
WebSpy - A simple CLI web scraping tool.

Commands:
    dump   - Extract and display main text content from a URL
    links  - Extract and categorize hyperlinks from a URL
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
import typer
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer(
    name="webspy",
    help="WebSpy - A simple CLI tool to scrape and inspect web pages.",
)
console = Console()

EXPORT_DIR = Path("exports")

# Tags that are typically not part of the "main content" of a page
NOISE_TAGS = [
    "script", "style", "nav", "footer", "header",
    "aside", "noscript", "form", "iframe", "svg",
    "button", "input", "select", "option", "label",
]

# Common selectors that usually wrap navigation / boilerplate
NOISE_SELECTORS = [
    "[role='navigation']",
    "[role='banner']",
    "[role='contentinfo']",
    ".nav", ".navbar", ".menu", ".sidebar",
    ".footer", ".header", ".cookie", ".advert", ".ads",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_page(url: str) -> requests.Response:
    """Fetch a URL with proper error handling. Exits the CLI on failure."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36 WebSpyBot/1.0"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.ConnectionError:
        console.print(
            f"[bold red]Connection Error:[/bold red] Could not connect to "
            f"'{url}'. Check the URL or your internet connection."
        )
        raise typer.Exit(code=1)
    except requests.exceptions.Timeout:
        console.print(
            f"[bold red]Timeout Error:[/bold red] The request to '{url}' "
            f"timed out."
        )
        raise typer.Exit(code=1)
    except requests.exceptions.HTTPError as e:
        console.print(
            f"[bold red]HTTP Error:[/bold red] {e} "
            f"(status code: {response.status_code})"
        )
        raise typer.Exit(code=1)
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Request Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def is_binary_asset(href: str) -> bool:
    """Check if a link points to an image/audio/video/binary file."""
    binary_extensions = (
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico",
        ".mp3", ".wav", ".ogg", ".flac",
        ".mp4", ".avi", ".mov", ".mkv", ".webm",
        ".pdf", ".zip", ".rar", ".7z", ".tar", ".gz",
        ".exe", ".dmg", ".apk",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    )
    path = urlparse(href).path.lower()
    return path.endswith(binary_extensions)


def get_file_label(href: str) -> str:
    """Return a friendly label like '[IMAGE] photo.jpg' for binary assets."""
    filename = os.path.basename(urlparse(href).path) or href
    ext = os.path.splitext(filename)[1].lower()

    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"}
    audio_exts = {".mp3", ".wav", ".ogg", ".flac"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    doc_exts = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
    archive_exts = {".zip", ".rar", ".7z", ".tar", ".gz"}

    if ext in image_exts:
        tag = "IMAGE"
    elif ext in audio_exts:
        tag = "AUDIO"
    elif ext in video_exts:
        tag = "VIDEO"
    elif ext in doc_exts:
        tag = "DOCUMENT"
    elif ext in archive_exts:
        tag = "ARCHIVE"
    else:
        tag = "FILE"

    return f"[{tag}] {filename}"


def extract_main_text(soup: BeautifulSoup) -> str:
    """Strip out noise tags/selectors and return cleaned readable text."""
    # Remove obvious noise tags
    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove elements matching noise selectors (nav bars, footers, ads, etc.)
    for selector in NOISE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    # Prefer <main>, <article>, or common content containers if present
    main_candidates = soup.find_all(["main", "article"])
    if not main_candidates:
        main_candidates = soup.select(
            "#content, .content, #main, .main, .post, .post-content, .entry-content"
        )

    target = main_candidates[0] if main_candidates else soup.body or soup

    # Extract text block by block, preserving paragraph structure
    blocks = []
    for element in target.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]
    ):
        text = element.get_text(separator=" ", strip=True)
        if not text:
            continue

        if element.name.startswith("h"):
            level = int(element.name[1])
            prefix = "#" * level
            blocks.append(f"\n{prefix} {text}\n")
        elif element.name == "li":
            blocks.append(f"- {text}")
        elif element.name == "blockquote":
            blocks.append(f"> {text}")
        elif element.name == "pre":
            blocks.append(f"```\n{text}\n```")
        else:
            blocks.append(text)

    if not blocks:
        # Fallback: just grab whatever text remains
        raw = target.get_text(separator="\n", strip=True)
        blocks = [line for line in raw.splitlines() if line.strip()]

    # Collapse excessive whitespace
    cleaned = "\n\n".join(blocks)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def make_export_filename(url: str, suffix: str, extension: str) -> Path:
    """Generate a safe filename inside the exports folder."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "_")
    path_part = re.sub(r"[^a-zA-Z0-9]+", "_", parsed.path).strip("_")
    name = f"{domain}_{path_part}_{suffix}" if path_part else f"{domain}_{suffix}"
    name = name.strip("_") + extension
    return EXPORT_DIR / name


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def dump(
    url: str = typer.Argument(..., help="The URL of the webpage to scrape."),
    export: bool = typer.Option(
        False, "--export", "-e",
        help="Save the extracted content to a Markdown file in 'exports/' instead of printing only."
    ),
):
    """
    Fetch a webpage and print its main text content,
    ignoring navigation, headers, footers, and scripts.
    """
    console.print(f"[bold cyan]Fetching:[/bold cyan] {url}")
    response = fetch_page(url)

    soup = BeautifulSoup(response.text, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else "Untitled Page"
    content = extract_main_text(soup)

    if not content:
        console.print("[yellow]No readable main content was found on this page.[/yellow]")
        raise typer.Exit(code=0)

    if export:
        file_path = make_export_filename(url, "dump", ".md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Source:** {url}\n\n")
            f.write("---\n\n")
            f.write(content)
            f.write("\n")
        console.print(f"[bold green]Saved to:[/bold green] {file_path}")
    else:
        console.print(Panel(f"[bold]{title}[/bold]", style="cyan"))
        console.print(Markdown(content))


@app.command()
def links(
    url: str = typer.Argument(..., help="The URL of the webpage to scrape for links."),
    export: bool = typer.Option(
        False, "--export", "-e",
        help="Save the link table to a text file in 'exports/' instead of printing only."
    ),
):
    """
    Fetch a webpage and list all hyperlinks, separated into
    Internal Links (same domain) and External Links.
    """
    console.print(f"[bold cyan]Fetching:[/bold cyan] {url}")
    response = fetch_page(url)

    soup = BeautifulSoup(response.text, "lxml")
    base_domain = urlparse(url).netloc

    internal_links = []
    external_links = []
    seen = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue

        full_url = requests.compat.urljoin(url, href)
        if full_url in seen:
            continue
        seen.add(full_url)

        link_domain = urlparse(full_url).netloc
        text = a_tag.get_text(strip=True) or "(no text)"

        if is_binary_asset(full_url):
            text = get_file_label(full_url)

        if link_domain == base_domain:
            internal_links.append((text, full_url))
        else:
            external_links.append((text, full_url))

    if export:
        file_path = make_export_filename(url, "links", ".txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Links extracted from: {url}\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"INTERNAL LINKS ({len(internal_links)})\n")
            f.write("-" * 60 + "\n")
            for text, link in internal_links:
                f.write(f"{text}\n    {link}\n")

            f.write(f"\nEXTERNAL LINKS ({len(external_links)})\n")
            f.write("-" * 60 + "\n")
            for text, link in external_links:
                f.write(f"{text}\n    {link}\n")

        console.print(f"[bold green]Saved to:[/bold green] {file_path}")
        return

    table = Table(title=f"Links found on {url}", show_lines=False)
    table.add_column("Type", style="bold", no_wrap=True)
    table.add_column("Text / Label", style="white")
    table.add_column("URL", style="dim")

    for text, link in internal_links:
        table.add_row("[green]Internal[/green]", text, link)

    for text, link in external_links:
        table.add_row("[magenta]External[/magenta]", text, link)

    if not internal_links and not external_links:
        console.print("[yellow]No links found on this page.[/yellow]")
        return

    console.print(table)
    console.print(
        f"\n[bold green]Internal:[/bold green] {len(internal_links)}   "
        f"[bold magenta]External:[/bold magenta] {len(external_links)}"
    )


if __name__ == "__main__":
    app()
