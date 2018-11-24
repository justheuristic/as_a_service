from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
long_description = open("./README.md").read()

version_string = '1.0.3'

setup(
    name="as_a_service",
    version=version_string,
    description="a simple tool to turn your function into a background service",
    long_description=long_description,

    # Author details
    author_email="justheuristic@gmail.com",
    url="https://github.com/justheuristic/as_a_service",

    # Choose your license
    license='MIT',
    packages=find_packages(),

    classifiers=[
        # Indicate who your project is intended for
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7 ',
        'Programming Language :: Python :: 3.4 ',
        'Programming Language :: Python :: 3.5 ',
        'Programming Language :: Python :: 3.6 ',
        'Programming Language :: Python :: 3.7 ',

    ],

    # What does your project relate to?
    keywords='service, background service, batched executor, parallel executor, background executor, background,' + \
             'deep learning, reinforcement learning',

    # List run-time dependencies here. These will be installed by pip when your project is installed.
    install_requires=[
        # nothing
    ],
)
