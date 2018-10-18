import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
        name="umptag",
        version="0.0.2",
        author="David Vaillant",
        author_email="david@vaillant.io",
        description="A tagging utility and package.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/D-Vaillant/umptag",
        packages=setuptools.find_packages(),
        python_requires='>=3.6',
        entry_points={
            'console_scripts': [
                'umptag = umptag.cli:main'
            ]
        }
)
