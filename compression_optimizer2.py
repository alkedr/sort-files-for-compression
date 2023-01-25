import math
import multiprocessing
import os
import random
import sys
import tarfile
import magic
import subprocess
import io
import zstd
from tqdm import tqdm


# def get_compressed_size(members):
#     with io.BytesIO() as output_tar_bytes_io:
#         with tarfile.open(fileobj=output_tar_bytes_io, mode='w:') as output_tar:
#             for member in members:
#                 # print(f'addfile {member.name}')
#                 output_tar.addfile(
#                     tarinfo=member,
#                     fileobj=input_tar.extractfile(member=member) if member.isfile() else None,
#                 )
#         output_tar_bytes_io.seek(0)
#         process_handle = subprocess.Popen(
#             args=['zstd', '-T0', '-5'],
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#         )
#         stdin = output_tar_bytes_io.read()
#         # print(f'len(stdin): {len(stdin)}')
#         return len(process_handle.communicate(input=stdin)[0])

def get_compressed_size(byte_array):
    return len(zstd.compress(byte_array))


def calc_combined_compressed_size(t):
    return t + (get_compressed_size(t[1] + t[3]),)


with tarfile.open(fileobj=sys.stdin.buffer, mode='r:', ignore_zeros=True) as input_tar:
    members = sorted(
        [
            member
            for member in input_tar.getmembers()
            if member.isfile()
        ],
        key=lambda m: -m.size,
    )

    members_extracted = [
        (member, input_tar.extractfile(member).read())
        for member in members
    ]

    all_pairs = [
        m1 + m2
        for m1 in members_extracted
        for m2 in members_extracted
        if m1 is not m2
    ]

    thread_pool = multiprocessing.Pool(processes=4)
    pairs = list(tqdm(
        thread_pool.imap_unordered(
            func=calc_combined_compressed_size,
            iterable=all_pairs,
        ),
        total=len(all_pairs)
    ))

    # for m1 in members:
    #     if not m1.isfile():
    #         continue
    #     m1_compressed_size = get_compressed_size(input_tar.extractfile(m1).read())
    #     best_ratio = 999_999_999_999
    #     for m2 in members:
    #         if not m2.isfile():
    #             continue
    #         if m1.name == m2.name:
    #             continue
    #         if m2.size < -best_ratio:
    #             continue
    #         m2_compressed_size = get_compressed_size(input_tar.extractfile(m2).read())
    #         m1m2_compressed_size = get_compressed_size(input_tar.extractfile(m1).read() + input_tar.extractfile(m2).read())
    #         # ratio = m1m2_compressed_size / (m1_compressed_size + m2_compressed_size)
    #         ratio = m1m2_compressed_size - (m1_compressed_size + m2_compressed_size)
    #
    #         if best_ratio > ratio:
    #             best_ratio = ratio
    #             print(f'{ratio:9} {m1.name} {m2.name} ({m1m2_compressed_size:_} - ({m1_compressed_size:_} + {m2_compressed_size:_})):', file=sys.stderr)
