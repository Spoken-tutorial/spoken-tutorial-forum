
# Getting started.

1. Create new database and import forums_empty.sql file from 'data' folder.
2. Create copy the `forums/config.sample.py` to `forums.config.py` and add the values accordingly.
3. To override any settings, create `forums/local_settings.py` and add the settings there.

# For Spam filter module

1. Install the required dependencies by running `pip install -r mlrequirements.txt`
2. On future edits in database and/or model scripts rerun the concerned files in the hosted environment.
    `python Spoken.py`
    `python OnlySpam.py`
