from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="houdini_meshy_plugin",
    version="1.0.0",
    author="Kevin @ FoxForm3D",
    author_email="contact@foxform3d.com",
    description="Plugin Houdini pour l'intégration de Meshy.ai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VoxelStudio/houdini_meshy_plugin",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "meshy_plugin=houdini_meshy_plugin.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "houdini_meshy_plugin": [
            "ui/*.ui",
            "resources/*.png",
            "resources/*.json",
            "config/*.json",
        ],
    },
) 