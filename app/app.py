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
                 '--semantics', 'tacitus']]

    err = ''
    data = request.get_json(force=True)['s'] + '\n'
    data = data.encode()

    for cmd in commands:
        try:
            p = sub.run(cmd, input=data, stdout=sub.PIPE,
                        stderr=sub.PIPE)
            data = p.stdout
        except Exception as e:
            err = 'Exception communicating with ' + cmd + '\n' + str(e)
            break

    out = data.decode()

    return json.dumps({'out': out, 'err': err})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
