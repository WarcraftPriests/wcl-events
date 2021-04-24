"""
python parse.py REPORTID FIGHTID
Given a Report and a Fight generate a list of simc event strings
"""

import os
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


def assure_path_exists(path):
    """Make sure the path exists and contains a folder"""
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


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

    raid_events = {
        "name": fight_data["name"],
        "keystone_level": fight_data["keystoneLevel"],
        "max_time": int(round((fight_data['end_time'] - fight_data['start_time'])/1000, 0)),
        "events": []
    }
    # Using the first events start time to calculate relative time for future events
    first_event_start_time = fight_data['dungeonPulls'][0]['start_time']

    if fight_data['dungeonPulls']:
        for pull in fight_data['dungeonPulls']:
            pull_duration_seconds = int(
                round((pull['end_time'] - pull['start_time'])/1000, 0))
            total_enemies = 0
            # TODO: right now we just take the enemy count and assume all are
            # active for the full duration of the pull, this will make non-linear
            # pulls or add spawns a problem
            for enemy in pull['enemies']:
                total_enemies += enemy[3]
            relative_start_time = int(
                round((pull['start_time'] - first_event_start_time)/1000, 0))
            # maybe add in x/y data relative to player? to pass to the raid event
            event = {
                "id": pull["id"],
                "name": pull["name"],
                "duration": pull_duration_seconds,
                "count": total_enemies,
                "startTime": relative_start_time,
            }
            raid_events["events"].append(event)
    return raid_events


def generate_simc_events(events):
    simc_events = []

    simc_events.append(
        f'raid_events+=/invulnerable,cooldown={events["max_time"]},duration={events["max_time"]},retarget=1')
    simc_events.append(f'max_time={events["max_time"]}')
    # TODO: maybe use duration_stddev
    for event in events["events"]:
        simc_events.append(
            f'raid_events+=/adds,name={event["name"].replace(",", "").replace(" ", "_")},count={event["count"]},duration={event["duration"]},cooldown={events["max_time"]},first={event["startTime"]}')
    return simc_events


def main():
    parser = argparse.ArgumentParser(
        description="Pulls fights from WCL to get SimC raid events")
    parser.add_argument('report', help='Report ID to generate events from')
    parser.add_argument('fight', help='Fight ID to generate events from')
    parser.add_argument(
        '--print', help='Prints output to stdout.', action='store_true')

    args = parser.parse_args()

    data = wcl_get_fight(args.report, args.fight)
    events = parse_raid_event(data)
    simc_events = generate_simc_events(events)

    if args.print:
        for event in simc_events:
            print(event)

    assure_path_exists('output/')
    with open("output/raid_events.simc", "w+") as file:
        for event in simc_events:
            file.writelines(event + "\n")
        file.close()


if __name__ == "__main__":
    main()
