from setuptools import setup, find_packages

setup(

    name='term3d',

    version='0.0.1',

    description='A 3D rendering engine for the terminal.',

    author='baod[nobucketdev]',
    author_email='baodvn@proton.me',

    packages=find_packages(),

    install_requires=[
    ],


    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Environment :: Console',
    ],
    python_requires='>=3.6',
)