from setuptools import setup, find_packages

setup(
    name='github2file',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'github2file = github2file.github2file:main'
        ]
    },
    install_requires=[
        'requests',
    ],
    author='Your Name',
    author_email='your_email@example.com',
    description='A tool to download and process files from a GitHub repository',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/github2file',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
