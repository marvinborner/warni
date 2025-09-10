# warni

> sends notifications for Biwapp/ARS/DWD/Katwarn/LHP/Mowas/Police
> warnings in your area

## installation

``` bash
cp .env.example .env
$EDITOR .env

virtualenv -p python venv
. venv/bin/activate
pip install -r requirements.txt
python warni.py &

# to install globally:
pip install .
warni &
```
