import csv
import json
import os
import numpy as np
import time
import argparse
import yaml


class LogWriter(object):
    # kind of inspired form openai.baselines.bench.monitor
    # We can add here an optional Tensorboard logger as well
    def __init__(self, path, keys, header="", name="monitor.csv"):
        self.keys = tuple(keys) + ("t",)
        assert path is not None

        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, name)
        if os.path.exists(filename):
            os.remove(filename)

        print("Writing logs to ", filename)

        self.f = open(filename, "wt")
        if isinstance(header, dict):
            header = "# {} \n".format(json.dumps(header))
        self.f.write(header)
        self.logger = csv.DictWriter(self.f, fieldnames=self.keys)
        self.logger.writeheader()
        self.f.flush()
        self.tstart = time.time()

    def write_row(self, epinfo):
        if self.logger:
            t = time.time() - self.tstart
            epinfo["t"] = t
            self.logger.writerow(epinfo)
            self.f.flush()


class LoadFromFile(argparse.Action):
    # parser.add_argument('--file', type=open, action=LoadFromFile)
    def __call__(self, parser, namespace, values, option_string=None):
        if values.name.endswith("yaml") or values.name.endswith("yml"):
            with values as f:
                namespace.__dict__.update(yaml.load(f, Loader=yaml.FullLoader))
                return

        with values as f:
            input = f.read()
            input = input.rstrip()
            for lines in input.split("\n"):
                k, v = lines.split("=")
                typ = type(namespace.__dict__[k])
                v = typ(v) if typ is not None else v
                namespace.__dict__[k] = v


def save_argparse(args, filename, exclude=None):
    if filename.endswith("yaml") or filename.endswith("yml"):
        if isinstance(exclude, str):
            exclude = [
                exclude,
            ]
        args = args.__dict__.copy()
        for exl in exclude:
            del args[exl]
        with open(filename, "w") as fout:
            yaml.dump(args, fout)
    else:
        with open(filename, "w") as f:
            for k, v in args.__dict__.items():
                if k is exclude:
                    continue
                f.write(f"{k}={v}\n")


def converter_xyz_output(input_file, output_file, z=None):
    from moleculekit.periodictable import periodictable_by_number
    # it gets the embedding data from the mol.z attribute
    mol_elements = np.array(z)
    npy_file = np.load(input_file)
    Nsteps = npy_file.shape[2]
    Nats = npy_file.shape[0]
    for i in range(Nsteps):
        with open(output_file, "a") as f:
            if "forces" not in input_file:
                f.write(str(Nats))
            f.write("\n\n")
            for j in range(Nats):
                if "forces" not in input_file:
                    f.write(periodictable_by_number[mol_elements[j]].symbol)
                    f.write(" ")
                for k in range(3):
                    f.write(str(npy_file[j, k, i]))
                    f.write(" ")
                f.write("\n")
