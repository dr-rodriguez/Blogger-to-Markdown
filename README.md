# Blogger to Markdown

I wanted to get my blog posts into markdown format for use in other projects, but was running into issues with outdated example scripts.
This script is a simple way to convert your Blogger XML feed to markdown.
This has been written and tested in 2025 and used some AI assistance to help me get started.

## Instructions

### Export your blog

Export a backup of your blog from Blogger. Go to Settings -> Manage Blog -> Backup Content. 
You'll get sent to a Google page that prepares the download for you and emails you when ready. 
The file will be a zip file with a structure like:

```
Blogger/
  - Blogs/
    - BlogName/
      - feed.atom
      - otherfiles...
    - Albums/
    - Comments/
    - Profile/
```

You'll want to grab the `feed.atom` file.

### Install the dependencies

I recommend using `uv` to install the dependencies. This has been tested on Windows and should work on other platforms.
```bash
uv sync
```

### Configure the script

Open the `src/main.py` file and configure the `BLOG_FILE` and `OUTPUT_DIR` variables.
If you want to use a different template, you can change the `TEMPLATE_FILE` variable.

### Run the script

```bash
uv run python src/main.py
```

This will create time-stamped markdown files in the `output` directory, one for each post.

### Review the output

You'll want to review the output and make sure it looks good. 
There could be errors depending on the structure of your posts or if you use custom scripts, but for the most part it should work.
