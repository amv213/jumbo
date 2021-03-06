import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="jumbo",
    version="1.0.2",
    description="A psycopg2 PostgreSQL wrapper for data science",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alvise Vianello",
    author_email="alvise@vianello.ai",
    url="https://gitlab.com/amv213/jumbo",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        ],
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'eventlet',
        'numpy',
        'pandas',
        'psycopg2',
        'pygtail',
        'python-dotenv',
        'sqlalchemy',
        'watchdog',
    ],
    extras_require={
            "doc": [
                'myst-parser',
                'sphinx',
                'sphinx-book-theme',
                'sphinx-copybutton',
                'sphinx-togglebutton',
                'sphinx-panels',
            ],
        },
)

# to build the package run the following:
# python setup.py sdist bdist_wheel
# python -m twine check dist/*
