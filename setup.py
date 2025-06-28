from setuptools import setup, Extension

# Define the extension module
libwords = Extension(
    'tboggle/libwords',
    sources=['src/tboggle/libwords.c'],  # Adjust the source path according to your project structure
    extra_compile_args=['-fPIC'],
    # extra_link_args=['-shared']
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
