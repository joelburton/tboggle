from setuptools import setup, Extension

# Define the extension module
libwords = Extension(
    'tboggle.libwords',
    sources=['libwords.c'],
    #extra_compile_args=['-O3'],
)

setup(
    name='tboggle',
    version='0.1',
    ext_modules=[libwords],
    entry_points={
        'console_scripts': [
            'tboggle=tboggle.boggle:main',
        ],
    },
    package_data={
        'tboggle': ['*.sqlite3','*.css', '*.dat'],  # Include all .sqlite3 and .dat files
    },
)
