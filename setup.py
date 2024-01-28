from setuptools import setup, find_packages

setup(
    name="distinguishedname",
    version="1.0.0",
    description="Parse and print RFC 2253 Distinguished Names",
    py_modules=['distinguishedname'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
