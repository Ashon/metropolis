import setuptools

setuptools.setup(
    name="metropolis",
    version=open('version').read().strip(),
    license='MIT',
    author="ashon lee",
    author_email="ashon8813@gmail.com",
    description="NATS message based microservice framework",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/ashon/metropolis",
    packages=setuptools.find_packages(exclude=['example']),
    install_requires=open('requirements.txt').readlines(),
    python_requires='>=3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
)
