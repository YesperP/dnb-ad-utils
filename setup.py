from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='dnb-ad-utils',
    version='0.1.7',
    license='MIT',
    author="Jesper Pedersen",
    author_email='Jesper.Pedersen@dnb.no, jes.ped.til@gmail.com',
    url="https://github.com/YesperP/dnb-ad-utils",
    description='Login to AWS and BitBucket through Azure Active Directory',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "boto3==1.24.*",
        "pyppeteer==0.2.*",
        "python-dateutil",
        "awscli",
        "pexpect",
        "setuptools",
        "sshconf"
    ],
    extras_require={
        'keyring': ['keyring']
    },
    entry_points={
        "console_scripts": [
            "awsad = dnbad.cli_awsad:main",
            "gproxy = dnbad.cli_gproxy:main"
        ],
    },
    python_requires='>=3.7'
)
