from setuptools import setup, find_packages

setup(
    name="ag-docs-sync",
    version="1.0.3",
    description="Universal Documentation & Session Archiver for Google Antigravity (Antigravity 2.0, CLI, IDE, and SDK)",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Don Sony",
    author_email="support@infuse.ae",
    url="https://github.com/donsony/ag-ext-docs",
    packages=find_packages(include=["ag_docs_sync", "ag_docs_sync.*"]),
    py_modules=[],
    include_package_data=True,
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Documentation",
    ],
    entry_points={
        "console_scripts": [
            "ag-docs-sync=scripts.sync_docs:main",
        ],
    },
)
