import math
import os
import random
import sys
import tarfile
import magic
import subprocess
import io


def get_compressed_size(members):
    with io.BytesIO() as output_tar_bytes_io:
        with tarfile.open(fileobj=output_tar_bytes_io, mode='w:') as output_tar:
            for member in members:
                # print(f'addfile {member.name}')
                output_tar.addfile(
                    tarinfo=member,
                    fileobj=input_tar.extractfile(member=member) if member.isfile() else None,
                )
        output_tar_bytes_io.seek(0)
        process_handle = subprocess.Popen(
            args=['zstd', '-T0', '-5'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        stdin = output_tar_bytes_io.read()
        # print(f'len(stdin): {len(stdin)}')
        return len(process_handle.communicate(input=stdin)[0])


with tarfile.open(fileobj=sys.stdin.buffer, mode='r:', ignore_zeros=True) as input_tar:
    members = input_tar.getmembers()
    best_size = sum([member.size for member in members])
    while True:
        i = random.randint(0, len(members)-1)
        j = random.randint(0, len(members)-1)
        if i == j or not members[i].isfile() or not members[j].isfile():
            continue
        print(f'Trying to swap files {i} and {j}', file=sys.stderr)
        tmp = members[i]
        members[i] = members[j]
        members[j] = tmp

        new_size = get_compressed_size(members)
        if best_size > new_size:
            print(f'{best_size:_} ({new_size - best_size})', file=sys.stderr)
            best_size = new_size
        else:
            tmp = members[i]
            members[i] = members[j]
            members[j] = tmp
