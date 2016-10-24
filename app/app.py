#!/usr/bin/env python3

import json

import subprocess as sub

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def main():
    return None

@app.route('/parse', methods=['POST'])
def parse():
    commands = [['/interpret/ext/candc/bin/t', '--stdin'],
                ['/interpret/ext/candc/bin/soap_client',
                 '--url', 'localhost:8888'],
                ['/interpret/ext/candc/bin/boxer', '--stdin',
                 '--semantics=fol']]

    err = ''
    data = request.get_json(force=True)['s'].encode()

    for cmd in commands:
        try:
            p = sub.run(cmd, input=data, stdout=sub.PIPE,
                        stderr=sub.PIPE)
            print()
            print(data)
            print(p)
            print()
            data = p.stdout
        except Exception as e:
            err = 'Exception communicating with ' + cmd + '\n' + str(e)
            break

    return json.dumps({'out': str(data), 'err': err})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
