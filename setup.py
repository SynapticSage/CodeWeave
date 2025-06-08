from setuptools import setup, find_packages

setup(
    name='codeweave',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'codeweave = codeweave.main:main',
            'cw = codeweave.main:main'
        ]
    },
    install_requires=[
        'requests',
        'certifi==2024.2.2',
        'charset-normalizer==3.3.2',
        'idna==3.6',
        'requests==2.31.0',
        'tk==0.1.0',
        'urllib3==2.2.1',
        'tqdm',
        'nbformat',
        'nbconvert',
        'pdfminer.six',
    ],
    tests_require=['pytest'],
    test_suite='pytest',
    author='Your Name',
    author_email='your_email@example.com',
    description='CodeWeave - Intelligent source code aggregation and AI workflow optimization',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/codeweave',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
