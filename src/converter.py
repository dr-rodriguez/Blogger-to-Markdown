import os
import xml.etree.ElementTree as ET
from html import unescape

import html2text
from utils import slugify, format_date, load_template, extract_first_image


# Namespaces
ATOM_NS = "{http://www.w3.org/2005/Atom}"
BLOGGER_NS = "{http://schemas.google.com/blogger/2018}"


def parse_blogger_xml(file_path):
    """Parse the Blogger XML file and return the root element."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root


def html_to_markdown(html_content):
    """Convert HTML content to markdown."""
    if not html_content:
        return ""
    
    # Unescape HTML entities
    html_content = unescape(html_content)
    
    # Configure html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    
    # Convert to markdown
    markdown = h.handle(html_content)
    return markdown.strip()


def extract_entry_data(entry):
    """Extract all relevant data from an entry element."""
    # Title
    title_elem = entry.find(f"{ATOM_NS}title")
    title = title_elem.text if title_elem is not None and title_elem.text else ""
    
    # Published date
    published_elem = entry.find(f"{ATOM_NS}published")
    published = published_elem.text if published_elem is not None and published_elem.text else ""
    date = format_date(published)
    
    # Author
    author_elem = entry.find(f"{ATOM_NS}author")
    author = ""
    if author_elem is not None:
        name_elem = author_elem.find(f"{ATOM_NS}name")
        author = name_elem.text if name_elem is not None and name_elem.text else ""
    
    # Categories (tags)
    categories = []
    for category in entry.findall(f"{ATOM_NS}category"):
        term = category.get("term")
        if term:
            categories.append(term)
    
    category = categories[0] if categories else ""
    taglist = ", ".join(categories) if categories else ""
    
    # Description
    desc_elem = entry.find(f"{BLOGGER_NS}metaDescription")
    description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
    
    # Content
    content_elem = entry.find(f"{ATOM_NS}content")
    html_content = content_elem.text if content_elem is not None and content_elem.text else ""
    
    # Extract first image
    image_path = extract_first_image(html_content)
    
    # Convert HTML to markdown
    markdown_content = html_to_markdown(html_content)
    
    # Generate filename
    title_slug = slugify(title)
    filename = f"{date}-{title_slug}.md" if date and title_slug else f"{title_slug}.md" if title_slug else "post.md"
    
    return {
        "title": title,
        "date": date,
        "author": author,
        "category": category,
        "tags": taglist,
        "description": description,
        "image_path": image_path,
        "content": markdown_content,
        "filename": filename,
    }


def convert_to_markdown(root, output_dir, template_file):
    """Go through each entry in the XML and convert it to Markdown."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load template
    template = load_template(template_file)
    
    # Find all entry elements
    entries = root.findall(f"{ATOM_NS}entry")
    
    print(f"Found {len(entries)} entries to convert...")
    
    for entry in entries:
        # Check if this is a POST entry (not a comment or other type)
        type_elem = entry.find(f"{BLOGGER_NS}type")
        if type_elem is None or type_elem.text != "POST":
            continue
        
        # Extract data from entry
        data = extract_entry_data(entry)
        
        # Replace template placeholders
        markdown_content = replace_template_placeholders(template, data)
        
        # Write to file
        output_path = os.path.join(output_dir, data["filename"])
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Converted: {data['filename']}")
    
    print(f"\nConversion complete! Files saved to {output_dir}/")


def replace_template_placeholders(template, data):
    """Replace template placeholders with actual data."""
    content = template
    content = content.replace("POST TITLE", data["title"])
    content = content.replace("DATE", data["date"])
    content = content.replace("IMAGE PATH", data["image_path"])
    content = content.replace("TAGLIST", data["tags"])
    content = content.replace("CATEGORY", data["category"])
    content = content.replace("AUTHOR", data["author"])
    content = content.replace("DESCRIPTION", data["description"])
    content = content.replace("<!-- POST CONTENT -->", data["content"])
    return content
