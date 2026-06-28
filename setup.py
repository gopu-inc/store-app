# setup.py
"""Setup pour StoreApp.TUI"""

from setuptools import setup, find_packages
import os

# Lire le README
readme = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

setup(
    name="storeapp-tui",
    version="1.0.0",
    description="StoreApp.TUI - Le Play Store du Terminal",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Mauricio-100",
    author_email="ceoseshell@gmail.com",
    url="https://github.com/gopu-inc/store-app",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "store": ["styles/*.tcss"],
        "screens": ["*.py"],
        "widgets": ["*.py"],
    },
    install_requires=[
        "textual>=0.50.0",
        "rich>=13.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "store = store.store:main",
            "agent = store.agent_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Terminals",
        "Topic :: Software Development :: User Interfaces",
    ],
)
