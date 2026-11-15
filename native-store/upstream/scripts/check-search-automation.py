"""Run the existing real-browser blog acceptance against the scoped search release."""
from pathlib import Path
import importlib.util
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('search_blog_browser',R/'tests/browser/blog.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.E=R/'artifacts/search-automation-20261112';m.main()
