from setuptools import setup, find_packages
import pathlib

# Read the contents of README file
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="xmu-rollcall-cli",
    version="3.1.4",
    packages=find_packages(),
    include_package_data=True,

    # Metadata
    author="KrsMt",
    author_email="krsmt0113@gmail.com",  # 建议填写真实邮箱
    description="XMU Rollcall Bot CLI - Automated rollcall monitoring and answering for Xiamen University Tronclass",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KrsMt-0113/XMU-Rollcall-Bot",
    project_urls={
        "Bug Reports": "https://github.com/KrsMt-0113/XMU-Rollcall-Bot/issues",
        "Source": "https://github.com/KrsMt-0113/XMU-Rollcall-Bot",
    },

    # Requirements
    python_requires=">=3.7",
    install_requires=[
        "requests",
        "pycryptodome",
        "xmulogin",
        "click>=8.1.0",
        "aiohttp>=3.9.0",
    ],

    # Entry points
    entry_points={
        "console_scripts": [
            "XMUrollcall-cli=xmu_rollcall.cli:cli",
        ],
    },

    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Education",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],

    # Keywords
    keywords="xmu xiamen-university rollcall tronclass automation cli",

    # License
    license="MIT",
)

