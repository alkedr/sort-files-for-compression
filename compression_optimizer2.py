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


def calc_combined_compressed_size_for_all_pairs_starting_with_file(t):
    tar_bytes, i = t

    tar_bytes_io = io.BytesIO()
    tar_bytes_io.write(tar_bytes)
    tar_bytes_io.seek(0)
    with tarfile.open(fileobj=tar_bytes_io, mode='r:', ignore_zeros=True) as input_tar:
        members = [
            member
            for member in input_tar.getmembers()
            if member.isfile()
        ]

        i_bytes = input_tar.extractfile(members[i]).read()

        result = []
        for j in range(len(members)):
            if i == j:
                continue
            j_bytes = input_tar.extractfile(members[j]).read()
            result.append((i, j, get_compressed_size(i_bytes + j_bytes)))

    return result


def main():
    tar_bytes = sys.stdin.buffer.read()
    tar_bytes_io = io.BytesIO()
    tar_bytes_io.write(tar_bytes)
    tar_bytes_io.seek(0)
    with tarfile.open(fileobj=tar_bytes_io, mode='r:', ignore_zeros=True) as input_tar:
        members = [
            member
            for member in input_tar.getmembers()
            if member.isfile()
        ]
        members = members

        thread_pool = multiprocessing.Pool(processes=4)
        pairs = list(tqdm(
            thread_pool.imap_unordered(
                func=calc_combined_compressed_size_for_all_pairs_starting_with_file,
                iterable=zip([tar_bytes] * min(len(members), 40000), range(len(members))),
            ),
            total=len(members)
        ))

        i_to_best_j_tuple = {}
        for sublist in pairs:
            for pair in sublist:
                i, j, combined_compressed_size = pair
                if i not in i_to_best_j_tuple or i_to_best_j_tuple[i][2] > pair[2]:
                    i_to_best_j_tuple[i] = pair

        for i in i_to_best_j_tuple:
            _, j, combined_compressed_size = i_to_best_j_tuple[i]
            i_compressed_size = get_compressed_size(input_tar.extractfile(members[i]).read())
            j_compressed_size = get_compressed_size(input_tar.extractfile(members[j]).read())
            win = combined_compressed_size - (i_compressed_size + j_compressed_size)
            print(
                f'{win} {members[i].name} {members[j].name}',
                file=sys.stderr)

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

main()