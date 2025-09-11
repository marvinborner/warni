# warni

> sends notifications for Biwapp/ARS/DWD/Katwarn/LHP/Mowas/Police
> warnings in your area

## installation

``` bash
virtualenv -p python venv
. venv/bin/activate
pip install -r requirements.txt
python warni.py &

# to install globally:
pipx install .

# to run perpetually:
setsid -f warni &
```

warni asks you some questions on the first run and stores the
configuration in your config directory
(e.g. `~/.config/warni/config.toml`)
