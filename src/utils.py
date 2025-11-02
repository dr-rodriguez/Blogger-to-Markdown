import re
from datetime import datetime


def slugify(text):
    """Convert text to a URL-safe slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


def format_date(date_string):
    """Format ISO 8601 date string to date-only format (strip timestamps)."""
    if not date_string:
        return ""
    
    try:
        # Parse ISO 8601 date
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        # Return just the date part
        return dt.strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return ""


def load_template(template_file):
    """Load the template file."""
    with open(template_file, 'r', encoding='utf-8') as f:
        return f.read()


def extract_first_image(html_content):
    """Extract the first image URL from HTML content."""
    if not html_content:
        return ""
    
    # Look for img tags with src attribute
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    match = re.search(img_pattern, html_content, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""