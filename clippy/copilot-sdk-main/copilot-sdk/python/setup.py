from setuptools import find_packages, setup

setup(
    name="github-copilot-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dateutil>=2.9.0.post0",
        "pydantic>=2.13.4",
        "typing-extensions>=4.15.0",
    ],
    python_requires=">=3.9",
)
