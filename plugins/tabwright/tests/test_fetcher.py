from tabwright.fetcher import html_to_markdown

SAMPLE_HTML = """
<html>
<head><style>body { color: red; }</style></head>
<body>
  <nav>Skip nav</nav>
  <header>Skip header</header>
  <main>
    <h1>Main Title</h1>
    <p>This is the content paragraph.</p>
    <ul><li>Item one</li><li>Item two</li></ul>
  </main>
  <footer>Skip footer</footer>
  <script>alert('skip')</script>
</body>
</html>
"""

def test_extracts_main_content():
    md = html_to_markdown(SAMPLE_HTML)
    assert "Main Title" in md
    assert "content paragraph" in md

def test_strips_boilerplate():
    md = html_to_markdown(SAMPLE_HTML)
    assert "Skip nav" not in md
    assert "Skip header" not in md
    assert "Skip footer" not in md
    assert "alert" not in md

def test_converts_list_to_markdown():
    md = html_to_markdown(SAMPLE_HTML)
    assert "Item one" in md
    assert "Item two" in md

def test_empty_html_returns_empty_string():
    md = html_to_markdown("")
    assert isinstance(md, str)
