import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="mcqq-tool",
    version="1.0.5",
    author="17TheWord",
    author_email="17theword@gmail.com",
    description="MC_QQ 工具包",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/17TheWord/mcqq-tool",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent"
    ]
)
