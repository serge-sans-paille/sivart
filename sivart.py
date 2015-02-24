#!/usr/bin/env python
# Copyright (c) 2014, Serge Guelton <serge.guelton@telecom-bretagne.eu> All
# rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

'''
A poor man's build farm
'''

import argparse
import itertools
import os
import re
import shutil
import sys
import traceback


__version__ = '0.2.1'

DEFAULT_CONFIG = '.sivart.yml'


def run_box_in_env(box_url, env, facets, vagrant_conf, identifier):
    '''
    Run a box described as a list of ``facets'' in the given ``env''
    '''

    from vagrant import Vagrant

    test_script = '{}.sh'.format(identifier)

    customize = sum([facet.get('customize', [""]) for facet in facets], [])
    box_customization = '\n'.join('p.customize {}'.format(c)
                                  for c in customize if c)

    def get_steps(step, facet):
        steps = facet.get(step, [])
        if isinstance(steps, str):
            steps = [steps]
        return steps

    steps = ["set -e"] + list(env)
    steps = sum([get_steps('install', facet) for facet in facets], steps)
    scripts = sum([get_steps('script', facet) for facet in facets], ['cd'])
    if scripts:
        unquoted = " && ".join(scripts)
        quoted = '"' + unquoted.replace('"', '"\\""') + '"'
        steps.append("su vagrant -c " + quoted)

    with open(test_script, 'w') as test_script_handle:
        test_script_handle.write("\n".join(steps))

    vagrantfile = 'Vagrantfile'
    shutil.rmtree(vagrantfile, ignore_errors=True)
    shutil.rmtree('.vagrant', ignore_errors=True)

    v = Vagrant(quiet_stdout=False)

    with open(vagrantfile, 'w') as vagrant_file:
        vagrant_file.write(vagrant_conf.format(box=box_url,
                                               customize=box_customization,
                                               test=test_script))
    print '*****', os.getcwd()
    v.up(provision=True)

    v.destroy()

    os.remove(test_script)
    os.remove(vagrantfile)
    shutil.rmtree('.vagrant')


def run(config_path, filtering_re, subs, keep, vagrant_conf):
    '''
    Run a full sivart configuration described in ``config_path'',
    pruning out boxes whose name does not match ``filtering_re''
    '''

    import yaml
    from vagrant import Vagrant

    errors = 0
    runs = 0
    config = yaml.load(open(config_path))

    # perform substitutions
    def run_subs(Key, Dict):
        Value = Dict[Key]
        if isinstance(Value, str):
            for sub, sub_value in subs.items():
                Value = Value.replace('%' + sub, sub_value)
            Dict[Key] = Value
        elif isinstance(Value, dict):
            for K in Value.keys():
                run_subs(K, Value)
        elif isinstance(Value, list):
            for i in range(len(Value)):
                run_subs(i, Value)

    run_subs(0, [config])

    # sanity checks
    for key, setup in config.items():
        if key.startswith('.'):
            assert 'box' not in setup, "facet cannot have a 'box' field"

    # run all boxes sequentially
    for key, setup in config.items():
        if key.startswith('.'):
            continue

        if not filtering_re.match(key):
            continue

        # retrieve one of the predefined box if available
        box_url = Vagrant.BASE_BOXES.get(setup['box'], setup['box'])

        facets_name = setup.get('using', [])
        if isinstance(facets_name, str):
            facets_name = [facets_name]

        facets = [config[facet_name] for facet_name in facets_name]
        facets.append(setup)

        envs = [facet.get('env', [""]) for facet in facets]

        # run the box in each environment
        for i, env in enumerate(itertools.product(*envs)):
            runs += 1
            try:
                run_box_in_env(box_url, env, facets,
                               vagrant_conf, "{}-{}".format(key, i))
            except Exception:
                print(traceback.format_exc())
                if not keep:
                    v = Vagrant(quiet_stdout=False)
                    v.destroy()
                errors += 1

    return errors, runs

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('config', default=DEFAULT_CONFIG, nargs='?',
                        help="config path")
    parser.add_argument('--filter', metavar='regexp', default=r'.*',
                        help="box filter regular expression")
    parser.add_argument('-D', '--define', metavar='var=value', action='append',
                        type=lambda s: s.split('=', 1), default=list(),
                        help="variable substitution")
    parser.add_argument('-k', '--keep', action='store_true',
                        help="do not destroy faulty vagrant boxes")

    args = parser.parse_args()

    vagrant_conf = '''
    VAGRANTFILE_API_VERSION = "2"

    Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
      config.vm.box = "{box}"
      config.vm.provision :shell, path: "{test}"
      # Providers
      config.vm.provider :virtualbox do |p|
        {customize}
      end
    end
    '''

    subs = dict(args.define)

    errors, runs = run(args.config,
                       re.compile(args.filter),
                       subs,
                       args.keep,
                       vagrant_conf)

    print("{} out of {} successful runs".format(runs - errors, runs))
    sys.exit(errors)
