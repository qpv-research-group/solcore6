from setuptools import setup

install_requires = []
tests_require = ["pytest", "pytest-cov"]
docs_require = []
extras_require = {
    "dev": tests_require + docs_require + ["pre-commit"],
    "docs": docs_require,
    "test": tests_require,
}


setup(
    name="solcore",
    version="6.0.0",
    description="Python-based solar cell simulator",
    url="https://github.com/qpv-research-group/solcore6",
    download_url="https://github.com/qpv-research-group/solcore6/archive/v6.0.0.tar.gz",
    project_urls={
        "Solcore research paper": "https://doi.org/10.1007/s10825-018-1171-3",
    },
    author="The Quantum Photovoltaics Group",
    author_email="d.alonso-alvarez@imperial.ac.uk",
    license="GNU General Public License",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    keywords="photovoltaics modelling physics",
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
)
