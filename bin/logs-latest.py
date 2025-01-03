#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2024-11-30 16:48:02

import sys
import os
import boto3
import json
import configparser
import datetime
EVENTS_LIMIT = 10

def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description="""\

""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument(
    "-r", "--max-requests", metavar="number", default =10, type=int,
    help="max requests to describe_log_groups, 1 request = 50 logGroups"
  )
  parser.add_argument(
    "-i", "--indent", metavar="number", default =2, type=int,
    help="indent of json output"
  )
  parser.add_argument(
    "-s", "--streams-limit", metavar="number", default =1, type=int,
    help="limit of streams to describe_log_streams"
  )
  parser.add_argument(
    "-d", "--dumps-limit", metavar="number", default =5, type=int,
    help="limit of dumps to output directory"
  )
  parser.add_argument("-w", "--required-words", metavar="word", nargs="*", help="require word in logGroupName")
  parser.add_argument(
    "-c", "--credentials", metavar="path",
    default=os.path.expanduser("~/.aws/credentials"), 
    help="path to the credentials file"
  )
  parser.add_argument(
    "-o", "--output", metavar="directory",
    default="latest_logs-"+datetime.datetime.now().strftime("%Y%m%d%H%M%S"), 
    help="output directory"
  )
  parser.add_argument("-n", "--no-credentials", action="store_true", help="no credentials file")
  # parser.add_argument("file", metavar="input-file", help="input file")
  options = parser.parse_args()
  # if not os.path.isfile(options.file): 
  #   raise Exception("The input file does not exist.") 
  return options

def main():
  options = parse_args()
  if options.no_credentials:
    client = boto3.client('logs')
  else:
    if not os.path.isfile(options.credentials):
      raise Exception("The credentials file does not exist.")
    else:
      with open(options.credentials, mode="r") as f:
        config = configparser.ConfigParser()
        config.read(options.credentials)
        client = boto3.client(
          "logs", 
          aws_access_key_id=config['default']['aws_access_key_id'], 
          aws_secret_access_key=config['default']['aws_secret_access_key']
        )
  del config
  # ロググループを取得
  log_groups = []
  init = True
  LIMIT = 50
  for i in range(options.max_requests):
    if init:
      _log_groups = client.describe_log_groups(limit=LIMIT)
      init = False
    else:
      _log_groups = client.describe_log_groups(limit=LIMIT, nextToken=_log_groups["nextToken"])
    log_groups.extend(_log_groups["logGroups"])
    if not _log_groups.get("nextToken"):
      break
  else:
    print("Too many loops")
    sys.exit()
  if options.required_words:
    for word in options.required_words:
      log_groups = [ group for group in log_groups if word in group['logGroupName'] ]

  # 各ロググループから最新のログを取得
  streams = []
  for group in log_groups:
    # print("========= gourp =========")
    # print(json.dumps(group, indent=2))
    log_group_name = group['logGroupName']
    _streams = client.describe_log_streams(
      logGroupName=log_group_name,
      orderBy='LastEventTime',
      descending=True,
      limit=options.streams_limit
    )
    # print("========= streams =========")
    # print(json.dumps(streams, indent=2))
    # print(datetime.fromtimestamp(streams["logStreams"][0]['lastIngestionTime']/1000))
    # print(datetime.fromtimestamp(streams["logStreams"][1]['lastIngestionTime']/1000))
    # print(datetime.fromtimestamp(streams["logStreams"][2]['lastIngestionTime']/1000))
    for s in _streams["logStreams"]:
      s["logGroupName"] = log_group_name
    if _streams["logStreams"]:
      streams.extend(_streams["logStreams"])
  # print(len(streams))
  # print(streams)
  streams = [ s for s in streams if "lastIngestionTime" in s.keys() ]  # lastIngestionTimeがないものは除外
  streams.sort(key=lambda x: x['lastIngestionTime'], reverse=True)
  latest_time = None
  for i, s in enumerate(streams):
    events = []
    # print("========= streams =========")
    # print(s['logGroupName'])
    if i == options.dumps_limit:
      break
    # print(s['logGroupName'])
    # print(datetime.datetime.fromtimestamp(s['lastIngestionTime']/1000))
    init = True
    for j in range(EVENTS_LIMIT):
      if init:
        _events = client.get_log_events(
          logGroupName=s['logGroupName'],
          logStreamName=s['logStreamName'],
          startFromHead=False,  # デフォルトだが明示的に指定
          # limit= 3
        )
        init = False
      else:
        _events = client.get_log_events(
          logGroupName=s['logGroupName'],
          logStreamName=s['logStreamName'],
          startFromHead=False,  # デフォルトだが明示的に指定
          nextToken=_events["nextBackwardToken"],
          # limit=3
        )
      events.extend(reversed(_events['events']))
      if not _events["events"]:
        break
    else:
      print("Too many loops")
      sys.exit()
    for e in events:
      e["timestamp"] = str(datetime.datetime.fromtimestamp(e["timestamp"]/1000))
      e["ingestionTime"] = str(datetime.datetime.fromtimestamp(e["ingestionTime"]/1000))
    if not os.path.isdir(options.output):
      os.makedirs(options.output)
    output_file = os.path.join(options.output, f"{i+1:04}.json")
    with open(output_file, "w") as f:
      f.write(
        json.dumps(
          {
            "logGroupName": s['logGroupName'],
            "logStreamName": s['logStreamName'],
            "events": list(reversed(events))
          },
          indent=options.indent
        )
      )
    # print(json.dumps(list(reversed(events)), indent=2))
    # sys.exit()

if __name__ == '__main__':
  main()
