import os
import xml.etree.ElementTree as ET

BLOG_FILE = "Blogger/Albums/StrakulsThoughts/feed.atom"
OUTPUT_DIR = "output"
TEMPLATE_FILE = "template.md"


def parse_blogger_xml(file_path):
    """Parse the Blogger XML file and return the root element."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root


def convert_to_markdown(root):
    """Go through each entry in the XML and convert it to Markdown."""
    pass


def main():
    print(f"Converting {BLOG_FILE} to Markdown...")
    root = parse_blogger_xml(BLOG_FILE)
    convert_to_markdown(root)


if __name__ == "__main__":
    main()
