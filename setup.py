import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jumbo",
    version="0.0.2",
    author="Alvise Vianello",
    author_email="alvise.vianello13@gmail.com",
    description="A psycopg2 PostgreSQL wrapper for scientists",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=[
        'eventlet',
        'loguru',
        'numpy',
        'sqlalchemy',
        'pandas',
        'psycopg2',
        'pygtail',
        'python-dotenv',
        'watchdog',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
