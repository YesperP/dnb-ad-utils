# GProxy and AwsAd
The projects include two programs, AwsAd and GProxy.

#### AwsAd
Generates STS Tokens based on SAML Assertion from Azure AD.
The credentials are stored in the AWS credentials files, such that it can be used by the aws cli, boto3, etc.
Multiple profiles are supported, giving the ability to use multiple AWS accounts.
Config for the profiles are stored in the AWS config file.

#### GProxy
Sets up an ssh local forward for the DNB bitbucket domain.
The forward is through a secure server, where the AzureAD login is used to authenticate.
* Automatically authenticates.
* Uses built in ssh.
* Auto configuration of ssh config.

#### Azure Active Directory 
* All MFA methods supported.
* Cookies are stored between sessions to support faster authentications, and less need of supplying password.
* Shared state between gproxy and awsad.

## Installation
Recommended: With password management (stores password in OS keystore).

    $ pip install "git+https://github.com/BobElvis/dnb-ad-utils.git#egg=dnb-ad-utils [keyring]"

Minimal:

    $ pip install git+https://github.com/BobElvis/dnb-ad-utils.git

## Requirements
* Python 3.7+

## Usage
There is one command for each of AwsAd and GProxy, with help files for each:
    
    $ gproxy -h
    $ awsad -h
    
Please use help to examine the subcommands for each program. Help will give more information for each subcommand. E.g:

    $ awsad login -h


## Configuration

Both GProxy and AwsAd needs some basic configuration before running, respectively:

    $ gproxy configure
    $ awsad configure [-p <profile>]

User and Password management for ActiveDirectory are shared between the two programs. 

## GProxy Inner Working
GProxy relies on OpenSSH on your local machine.
It will set up a local forward tunnel to route bitbucket through the server.
Configuration will check that (and add if missing) the following entry is present in config:

    Host git.tech-01.net
        Hostname XXXX  # Default: localhost
        Port XXXX  # Default: 9000
        StrictHostKeyChecking XX  # Default: no
