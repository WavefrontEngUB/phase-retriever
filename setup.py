from setuptools import setup, find_packages

setup(
    name='phase_retriever',
    version='0.1.4',
    long_description=open('README.md').read(),
    description="Program to retrieve the phase of an optic field based on Fineup's algorithm.",
    url='https://github.com/kramos966/phase-retriever',
    author='Marcos Aviñoá-Pérez',
    author_email='dmaluenda@ub.edu',
    license='GNU Public License v3',
    packages=find_packages(),
    install_requires=[open('requirements.txt').read().splitlines()],
    include_package_data=True,

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering'
    ],
)