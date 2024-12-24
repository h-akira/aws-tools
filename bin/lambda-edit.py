#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2024-09-02 20:38:09

# import sys
import os
import configparser
import boto3
import shutil
import requests

TEMPLATE = """\
import boto3

def lambda_handler(event, context): 
  print("Hello, world!")
"""

def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description="""\

""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-o", "--output", metavar="output-file", help="zip fie")
  parser.add_argument("-u", "--upload", action="store_true", help="upload function")
  parser.add_argument("-c", "--create", action="store_true", help="create function")
  parser.add_argument("-d", "--download", action="store_true", help="download function")
  parser.add_argument("-s", "--save-zip", action="store_true", help="don't remove zip file after upload")
  parser.add_argument(
    "--credentials", metavar="path",
    default=os.path.expanduser("~/.aws/credentials"), 
    help="path to the credentials file"
  )
  parser.add_argument("-n", "--no-credentials", action="store_true", help="no credentials file")
  parser.add_argument("function", metavar="lambda-function", help="lambda function name, that is the directory name")
  options = parser.parse_args()
  if [options.upload, options.create, options.download].count(True) > 1:
    raise Exception("Only one of -u, -c, -d can be used.")
  return options

def main():
  options = parse_args()
  if options.no_credentials:
    client = boto3.client('lambda')
  else:
    if not os.path.isfile(options.credentials):
      raise Exception("The credentials file does not exist.")
    else:
      with open(options.credentials, mode="r") as f:
        config = configparser.ConfigParser()
        config.read(options.credentials)
        client = boto3.client(
          "lambda", 
          aws_access_key_id=config['default']['aws_access_key_id'], 
          aws_secret_access_key=config['default']['aws_secret_access_key']
        )
        if options.create:
          accountID=boto3.client("sts").get_caller_identity()["Account"]
  del config
  try:
    function_info = client.get_function(FunctionName=options.function)
  except client.exceptions.ResourceNotFoundException:
    function_info = None
  if options.output:
    if options.output[-4:] != ".zip":
      raise Exception("The output file must be a zip file.")
  else:
    options.output = options.function+".zip"
  if options.upload or options.create:
    if function_info is None and options.upload:
      raise Exception("The function does not exist.")
    elif function_info is not None and options.create:
      raise Exception("The function already exists.")
    if not os.path.isdir(options.function):
      raise Exception("The directory does not exist.")
    if os.path.isfile(options.output):
      if "y" == input(f"File {options.output} exists. Overwrite? [y/other]"):
        os.remove(options.output)
    shutil.make_archive(options.output[:-4], 'zip', root_dir=options.function)
    with open(options.output, "rb") as f:
      if options.upload:
        client.update_function_code(
          FunctionName=options.function,
          ZipFile=f.read()
        )
      if options.create:
        client.create_function(
          FunctionName=options.function,
          Runtime="python3.13",
          Role=f"arn:aws:iam::{accountID}:role/role-tools-lambda-common",
          Handler='lambda_function.lambda_handler',
          Code={
            'ZipFile': f.read()
          },
          Timeout=5,
          MemorySize=128
        )
    if not options.save_zip:
      os.remove(options.output)
  else:
    if os.path.isdir(options.function):
      raise Exception("The directory exist.")
    if options.download:
      if function_info is None:
        raise Exception("The function does not exist.")
      with requests.get(client.get_function(FunctionName=options.function)['Code']["Location"], stream=True) as r:
        with open(options.output, "wb") as f:
          for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)
      shutil.unpack_archive(options.output, options.function)
      if not options.save_zip:
        os.remove(options.output)
    else:
      os.makedirs(options.function)
      with open(os.path.join(options.function, 'lambda_function.py'), 'w') as f:
        print(TEMPLATE, file=f)

if __name__ == '__main__':
  main()
