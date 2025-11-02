from converter import parse_blogger_xml, convert_to_markdown


BLOG_FILE = "Blogger/Blogs/StrakulsThoughts/feed.atom"
OUTPUT_DIR = "output"
TEMPLATE_FILE = "template.md"


def main():
    print(f"Converting {BLOG_FILE} to Markdown...")
    root = parse_blogger_xml(BLOG_FILE)
    convert_to_markdown(root, output_dir=OUTPUT_DIR, template_file=TEMPLATE_FILE)


if __name__ == "__main__":
    main()
