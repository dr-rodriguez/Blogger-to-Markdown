# Script to download images from blog posts
import os
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
ASSETS_DIR = os.getenv("ASSETS_DIR", "assets/img/posts")
LIMIT_FILES = int(os.getenv("LIMIT_FILES", 0))


def parse_frontmatter(content):
    """Parse frontmatter from markdown file and extract date."""
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    if not match:
        return None, content
    
    frontmatter = match.group(1)
    body = content[match.end():]
    
    # Extract date from frontmatter
    date_match = re.search(r'^date:\s*(.+?)$', frontmatter, re.MULTILINE)
    date_str = date_match.group(1).strip() if date_match else None
    
    return date_str, body


def convert_date_to_folder(date_str):
    """Convert YYYY-MM-DD date to YYYYMMDD folder format."""
    if not date_str:
        return None
    # Remove hyphens
    return date_str.replace('-', '')


def extract_image_urls_from_frontmatter(content):
    """Extract image URL from frontmatter img field."""
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    if not match:
        return []
    
    frontmatter = match.group(1)
    img_match = re.search(r'^img:\s*(.+?)$', frontmatter, re.MULTILINE)
    if img_match:
        img_url = img_match.group(1).strip()
        if img_url and img_url.startswith('http'):
            return [img_url]
    return []


def extract_image_urls_from_content(content):
    """Extract all image URLs from markdown content."""
    urls = set()
    
    # Pattern for markdown images: ![](url) or ![alt](url)
    pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
    urls.update(re.findall(pattern, content))
    
    # Pattern for linked images: [![](url1)](url2) - extract both URLs
    linked_pattern = r'\[!\[.*?\]\((https?://[^\)]+)\)\]\((https?://[^\)]+)\)'
    matches = re.findall(linked_pattern, content)
    for match in matches:
        urls.add(match[0])  # Image URL
        urls.add(match[1])  # Link URL (may be same or different)
    
    return list(urls)


def get_filename_from_url(url):
    """Extract filename from URL."""
    parsed = urlparse(url)
    # Get path and unquote to handle encoded characters
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    
    # If no filename in URL, try to get extension from content-type or use default
    if not filename or '.' not in filename:
        # Try to get extension from path
        if '.' in path:
            ext = os.path.splitext(path)[1]
            if ext:
                filename = f"image{ext}"
        else:
            filename = "image.jpg"  # Default fallback
    
    return filename


def download_image(url, save_path):
    """Download image from URL and save to path."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def normalize_path_for_markdown(path):
    """Normalize file path to use forward slashes for markdown compatibility."""
    return str(path).replace('\\', '/')


def update_markdown_file(file_path, url_mapping, date_folder):
    """Update markdown file with local image paths."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Update frontmatter img field
    frontmatter_pattern = r'^(---\s*\n.*?^img:\s*)(.+?)(\n.*?---\s*\n)'
    def replace_img(match):
        img_value = match.group(2).strip()
        if img_value in url_mapping:
            local_path = url_mapping[img_value]
            # Use shorter path format: posts/YYYYMMDD/filename
            short_path = f"posts/{date_folder}/{os.path.basename(local_path)}"
            return f"{match.group(1)}{short_path}{match.group(3)}"
        return match.group(0)
    
    content = re.sub(frontmatter_pattern, replace_img, content, flags=re.DOTALL | re.MULTILINE)
    
    # Update linked images first: [![](url1)](url2) - handle both URLs
    linked_pattern = r'\[(!\[.*?\]\((https?://[^\)]+)\))\]\((https?://[^\)]+)\)'
    def replace_linked_image(match):
        image_part = match.group(1)  # The ![](url) part
        img_url = match.group(2)
        link_url = match.group(3)
        
        # Extract alt text from image part
        alt_match = re.match(r'!\[(.*?)\]\(.+?\)', image_part)
        alt_text = alt_match.group(1) if alt_match else ""
        
        # Replace image URL if it's in mapping
        if img_url in url_mapping:
            local_path = normalize_path_for_markdown(url_mapping[img_url])
            image_part = f"![{alt_text}]({local_path})"
        
        # Replace link URL if it's in mapping, otherwise keep original
        if link_url in url_mapping:
            local_path = normalize_path_for_markdown(url_mapping[link_url])
            return f"[{image_part}]({local_path})"
        else:
            # Even if link_url isn't in mapping, return updated image_part if it was updated
            if img_url in url_mapping:
                return f"[{image_part}]({link_url})"
            return match.group(0)
    
    content = re.sub(linked_pattern, replace_linked_image, content)
    
    # Update standalone markdown image syntax: ![](url) or ![alt](url)
    pattern = r'!\[(.*?)\]\((https?://[^\)]+)\)'
    def replace_url(match):
        alt_text = match.group(1)
        url = match.group(2)
        if url in url_mapping:
            local_path = normalize_path_for_markdown(url_mapping[url])
            # Use full path: assets/img/posts/YYYYMMDD/filename
            full_path = local_path
            return f"![{alt_text}]({full_path})"
        return match.group(0)
    
    content = re.sub(pattern, replace_url, content)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Loop over all markdown files in the output directory and download the images."""
    output_path = Path(OUTPUT_DIR)
    if not output_path.exists():
        print(f"Output directory not found: {OUTPUT_DIR}")
        return
    
    # Find all markdown files
    markdown_files = list(output_path.glob("*.md"))
    total_files = len(markdown_files)
    
    # Limit files for testing/debugging if LIMIT_FILES is set
    if LIMIT_FILES > 0:
        markdown_files = markdown_files[:LIMIT_FILES]
        print(f"Found {total_files} markdown files (processing {len(markdown_files)} due to LIMIT_FILES={LIMIT_FILES})")
    else:
        print(f"Found {total_files} markdown files")
    
    # Track image URLs and which files reference them
    url_to_files = defaultdict(set)  # URL -> set of file paths
    file_to_urls = {}  # file path -> set of URLs
    file_to_date = {}  # file path -> date folder
    
    # First pass: extract all image URLs from all files
    print("\nExtracting image URLs from markdown files...")
    for md_file in markdown_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get date and convert to folder format
        date_str, body = parse_frontmatter(content)
        date_folder = convert_date_to_folder(date_str)
        if not date_folder:
            print(f"Warning: No date found in {md_file.name}, skipping")
            continue
        
        file_to_date[md_file] = date_folder
        
        # Extract image URLs
        urls = set()
        urls.update(extract_image_urls_from_frontmatter(content))
        urls.update(extract_image_urls_from_content(body))
        
        file_to_urls[md_file] = urls
        
        # Track which files use which URLs
        for url in urls:
            url_to_files[url].add(md_file)
    
    # Second pass: download unique URLs and map to local paths
    print("\nDownloading images...")
    url_to_local_path = {}  # URL -> local path
    local_path_to_url = {}  # local path -> URL (reverse mapping to avoid duplicates)
    
    for url, files in url_to_files.items():
        # Skip if URL is already mapped
        if url in url_to_local_path:
            continue
        
        # Use the date folder from the first file that references this URL
        first_file = next(iter(files))
        date_folder = file_to_date[first_file]
        
        # Create date-stamped folder
        folder_path = Path(ASSETS_DIR) / date_folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Get filename and create local path
        filename = get_filename_from_url(url)
        local_path = folder_path / filename
        
        # Check if this exact file path is already mapped to this URL
        local_path_str = str(local_path)
        if local_path_str in local_path_to_url:
            # File exists and is mapped to a URL
            existing_url = local_path_to_url[local_path_str]
            if existing_url == url:
                # Same URL, reuse the mapping
                url_to_local_path[url] = local_path_str
                continue
            else:
                # Different URL mapped to this file, need different filename
                # Handle filename conflicts - find next available filename
                counter = 1
                name, ext = os.path.splitext(filename)
                while True:
                    local_path = folder_path / f"{name}_{counter}{ext}"
                    local_path_str = str(local_path)
                    if local_path_str not in local_path_to_url and not local_path.exists():
                        break
                    counter += 1
        elif local_path.exists():
            # File exists but not yet mapped - map it to this URL
            url_to_local_path[url] = str(local_path)
            local_path_to_url[str(local_path)] = url
            print(f"Using existing file: {local_path}")
            continue
        
        # Download only if file doesn't exist
        if not local_path.exists():
            print(f"Downloading {url} -> {local_path}")
            if download_image(url, local_path):
                url_to_local_path[url] = str(local_path)
                local_path_to_url[str(local_path)] = url
            else:
                print(f"Failed to download {url}")
    
    # Third pass: update markdown files with local paths
    print("\nUpdating markdown files with local image paths...")
    updated_count = 0
    for md_file, urls in file_to_urls.items():
        date_folder = file_to_date[md_file]
        # Build URL mapping for this file
        file_url_mapping = {url: url_to_local_path[url] for url in urls if url in url_to_local_path}
        
        if file_url_mapping:
            if update_markdown_file(md_file, file_url_mapping, date_folder):
                updated_count += 1
                print(f"Updated: {md_file.name}")
    
    print(f"\nComplete! Updated {updated_count} files with local image paths.")


if __name__ == "__main__":
    main()
