"""
Cost Melt Python SDK - Setup Script

Setup script for pip installation compatibility.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="costmelt",
    version="0.1.0",
    author="Cost Melt Team",
    author_email="support@costmelt.com",
    description="Official Python SDK for Cost Melt - LLM routing, caching, batching, and cost-optimization proxy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/costmelt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "typing-extensions>=4.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ],
    },
)

