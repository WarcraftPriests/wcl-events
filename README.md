# wcl-events
Parses WCL fights and converts it into SimC events

## How to use

```
python parse.py REPORTID FIGHTID
```

e.g. `python parse.py DCXQbaV8j26mxfwJ 237`

- REPORTID: Report ID for the log
- FIGHTID: Specific Fight ID that corresponds to the dungeon fight of a log.

### Secret
Create `api_secrets.py` in the root directory with the following contents:

```python
api_key = 'XXX'
```

You can go to [WCL](https://www.warcraftlogs.com/profile) to get your api key (scroll down on your profile page).