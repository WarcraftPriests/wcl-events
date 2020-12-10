"""
python parse.py REPORTID FIGHTID
Given a Report and a Fight generate a list of simc event strings
"""

import argparse
import importlib
import requests
import json

api_secrets_spec = importlib.util.find_spec("api_secrets")
if api_secrets_spec:
    api_secrets = api_secrets_spec.loader.load_module()

session = requests.Session()
session.headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Publik\'s WCL API Script'
}


def wcl_get_fight(report_id, fight_id):
    api_url = f'https://www.warcraftlogs.com:443/v1/report/fights/{report_id}/?api_key={api_secrets.api_key}'

    response = session.get(api_url)
    status = response.status_code

    if status == 200:
        data = json.loads(response.content)
        for fight in data['fights']:
            if str(fight['id']) == fight_id:
                return fight
    else:
        print(f'[!] [{status}] Server Error')


def parse_raid_event(fight_data):
    print(f'Analyzing {fight_data["name"]} +{fight_data["keystoneLevel"]}...')

    raid_events = []

    if fight_data['dungeonPulls']:
        for pull in fight_data['dungeonPulls']:
            pull_duration_seconds = int(
                round((pull['end_time'] - pull['start_time'])/1000, 0))
            total_enemies = 0
            for enemy in pull['enemies']:
                total_enemies += enemy[3]
            # maybe add in x/y data to pass to the raid event
            # TODO: add in downtime between pulls somehow to set spawn times
            event = {
                "id": pull["id"],
                "name": pull["name"],
                "duration": pull_duration_seconds,
                "count": total_enemies
            }
            raid_events.append(event)
    return raid_events


def generate_simc_events(events):
    simc_events = []

    # maybe use duration_stddev
    # TODO: add in params to set the adds to spawn sequentially
    for event in events:
        simc_events.append(
            f'raid_events+=/adds,name={event["name"].replace(" ", "_")},count={event["count"]},duration={event["duration"]},cooldown=1000')
    return simc_events


def main():
    parser = argparse.ArgumentParser(
        description="Pulls fights from WCL to get SimC raid events")
    parser.add_argument('report', help='Report ID to generate events from')
    parser.add_argument('fight', help='Fight ID to generate events from')
    args = parser.parse_args()

    data = wcl_get_fight(args.report, args.fight)
    events = parse_raid_event(data)
    simc_events = generate_simc_events(events)

    for event in simc_events:
        print(event)


if __name__ == "__main__":
    main()
