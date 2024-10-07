#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2024-10-07 21:27:19

import sys
import os
import random
import subprocess

def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description="""\
事前にpip3 install hoge -t targetとしてたうえで実行する
""", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-t", "--target", metavar="output-file", default="target", help="target path")
  parser.add_argument("-V", "--python-version", metavar="version", default="3.12", help="python version")
  # parser.add_argument("-", "--", action="store_true", help="")
  parser.add_argument("name", metavar="input-file", help="input file")
  options = parser.parse_args()
  return options

def main():
  options = parse_args()
  tem_dir = "tem-" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=8))
  os.makedirs(os.path.join(tem_dir, f"python/lib/python{options.python_version}/site-packages"))
  subprocess.run(f"rsync -av {os.path.join(options.target, '*')} {tem_dir}/python/lib/python{options.python_version}/site-packages/", shell=True)
  subprocess.run(["zip", "-r", os.path.abspath(os.path.join(tem_dir, "layer.zip")), "python"], cwd=tem_dir)
  subprocess.run(
    [
      "aws", 
      "lambda", 
      "publish-layer-version", 
      "--layer-name", 
      options.name, 
      "--zip-file", 
      f"fileb://{os.path.join(tem_dir, 'layer.zip')}",
      "--compatible-runtimes",
      f"python{options.python_version}"
    ]
  )
  subprocess.run(["rm", "-rf", tem_dir])

if __name__ == '__main__':
  main()
