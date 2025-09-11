from setuptools import setup

setup(
    name="warni",
    version="0.1",
    license="MIT",
    description="Sends notifications for Biwapp/ARS/DWD/Katwarn/LHP/Mowas/Police warnings in your area",
    author="Marvin Borner",
    author_email="git@marvinborner.de",
    py_modules=["warni"],
    install_requires=[
        "de-nina",
        "shapely",
        "notify_py",
        "python-dotenv",
        "platformdirs",
        "tomli-w",
    ],
    entry_points={
        "console_scripts": ["warni=warni:main"],
    },
)
