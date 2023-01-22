#!/bin/bash

set -eux

# TODO https://github.com/projg2/tar-reorder
# TODO https://github.com/zholos/tar-sorted

# Requires Docker, zstd, sudo, tens of gb of disk space, hours of time

print_compression_table_lines() {
  ORIGINAL_TAR="$1"
  REORDERED_TAR="$2"
  COMPRESSION="$3"
  ORIGINAL_COMPRESSED_SIZE="$($COMPRESSION < "$ORIGINAL_TAR" | wc --bytes)"
  printf "| original  | %-30s | %'13.0f |                    |\n" "$COMPRESSION" "$ORIGINAL_COMPRESSED_SIZE"
  REORDERED_COMPRESSED_SIZE="$($COMPRESSION < "$REORDERED_TAR" | wc --bytes)"
  printf "| reordered | %-30s | %'13.0f | %'18.0f |\n" "$COMPRESSION" "$REORDERED_COMPRESSED_SIZE" "$((REORDERED_COMPRESSED_SIZE - ORIGINAL_COMPRESSED_SIZE))"
}

measure_compression_for_image() (
  local IMAGE="$1"

  # Download docker image
  sudo rm -rf benchmark_tmp
  mkdir -p benchmark_tmp/docker_saved_image benchmark_tmp/extracted_archive benchmark_tmp/extracted_reordered_archive
  docker pull "$IMAGE"
  docker save "$IMAGE" | tar --extract --file=- --directory=benchmark_tmp/docker_saved_image

  # Extract all layers
  find benchmark_tmp/docker_saved_image -name 'layer.tar' -print0 \
    | xargs --null --max-lines=1 sudo tar --extract --same-owner --directory=benchmark_tmp/extracted_archive --file

  # Create archive.tar with all layers combined
  sudo tar --create --sort=name --file=benchmark_tmp/archive.tar --directory=benchmark_tmp/extracted_archive .

  # Create reordered_archive.tar by reordering archive.tar
  python3 sort_files_for_compression.py < benchmark_tmp/archive.tar > benchmark_tmp/reordered_archive.tar

  # Extract reordered_archive.tar and compare it to the original directory
  sudo tar --extract --same-owner --file=benchmark_tmp/reordered_archive.tar --directory=benchmark_tmp/extracted_reordered_archive
  sudo diff --recursive --brief --no-dereference benchmark_tmp/extracted_archive benchmark_tmp/extracted_reordered_archive \
    && echo 'No differences found between extracted original and extracted reordered'

  # Compress both original and reordered archives in a bunch of different ways and print the results
  set +x
  printf "%s\n" "$IMAGE"
  printf "|  Sorting  | Compression                    |     Size      | Delta (<0 is good) |\n"
  printf "|    ---    | ---                            |          ---: |               ---: |\n"
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'cat'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -1'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -2'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -3'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -4'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -5'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -6'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -7'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -8'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -9'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -10'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -16'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -22 --ultra'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar 'zstd -T0 -22 --ultra --long=31'
  print_compression_table_lines benchmark_tmp/archive.tar benchmark_tmp/reordered_archive.tar \
    'zstd -T0 -22 --ultra --long=31 --zstd=strat=9,windowLog=31,hashLog=30,chainLog=30,searchLog=30,minMatch=3,targetLength=131072,overlapLog=9,ldmHashLog=30'
)

measure_compression_for_image 'ubuntu:22.04'
#measure_compression_for_image 'nvidia/cuda:11.3.0-cudnn8-devel-ubuntu20.04'
