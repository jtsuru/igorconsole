from setuptools import setup
from igorconsole import __version__


setup(
    name="igorconsole",
    version=__version__,
    description='Allows seamless controlling if Igor Pro from python.',
    url='https://github.com/jtsuru/igorconsole',
    author="jtsuru",
    author_email="33685861+jtsuru@users.noreply.github.com",
    license='MIT',
    keywords='IgorPro',
    packages=["igorconsole", "igorconsole.abc", "igorconsole.oleconsole"],
    package_data={"igorconsole": ["oleconsole/config.ini", "styles/*.json"]},
    install_requires=[
        "numpy",
        "pywin32",
    ],
    extras_require={
        "plot": ["matplotlib"],
        "image": ["Pillow"],
        "dframe": ["pandas"],
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Win32 (MS Windows)",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
    ],
)
