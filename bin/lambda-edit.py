#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2024-09-02 20:38:09

import sys
import os
import subprocess

TEMPLATE = """\
import boto3

def lambda_handler(event, context): 
  print("Hello, world!")"""


def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description="""\

""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-o", "--output", metavar="output-file", help="zip fie")
  parser.add_argument("-u", "--upload", action="store_true", help="upload")
  parser.add_argument("-r", "--remove-zip", action="store_true", help="remove zip file after upload")
  parser.add_argument("directory", metavar="lambda-directory", help="lambda directory")
  options = parser.parse_args()
  return options

def main():
  options = parse_args()
  if options.upload:
    if not os.path.isdir(options.directory):
      raise Exception("The directory does not exist.")
    if not options.output:
      options.output = options.directory + '.zip'
    if os.path.isfile(options.output):
      if "y" == input(f"File {options.output} exists. Overwrite? [y/other]"):
        os.remove(options.output)
      else:
        return None
    subprocess.run(["zip", "-r", os.path.abspath(options.output), "."], cwd=options.directory)
    subprocess.run(["aws", "lambda", "update-function-code", "--function-name", options.directory, "--zip-file", f"fileb://{options.output}"])
    if options.remove_zip:
      os.remove(options.output)
  else:
    if os.path.isdir(options.directory):
      raise Exception("The directory exist.")
    os.makedirs(options.directory)
    with open(os.path.join(options.directory, 'lambda_function.py'), 'w') as f:
      print(TEMPLATE, file=f)

if __name__ == '__main__':
  main()
