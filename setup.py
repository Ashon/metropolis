import setuptools

setuptools.setup(
    name="metropolis",
    version="0.1.0",
    license='MIT',
    author="ashon lee",
    author_email="ashon8813@gmail.com",
    description="Microservice gateway using Nats",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/ashon/metropolis",
    packages=setuptools.find_packages(),
    install_requires=open('requirements.txt').readlines(),
    python_requires='>=3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
)
