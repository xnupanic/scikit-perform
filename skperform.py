"""
Copyright 2021 Jerrad M. Genson

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""

import os
import gzip
import tempfile
from time import time
from multiprocessing import Pool, cpu_count

import wget

import benchmarks

BENCHMARKS = {
    'locally linear embedding': (benchmarks.locally_linear_embedding, False),
    'random forest': (benchmarks.random_forest, True),
    'support vector machine': (benchmarks.support_vector_machine, True),
    'xml parsing': (benchmarks.xml_parsing, False),
    'lzma': (benchmarks.lzma_compression, False),
    'sha512': (benchmarks.sha512, False),
    'boyer-moore/horspool': (benchmarks.hamlet_word_count, True),
}


SINGLE_CORE_REFERENCE = 17.156576803752355
MULTI_CORE_REFERENCE = 33.75305533409119


def main():
    single_core_scores = []
    multi_core_scores = []
    for name, descriptor in BENCHMARKS.items():
        print(name, '(single-core): ', end='', flush=True)
        seconds = run_test(descriptor[0], 1)
        print(str(seconds), 'seconds')
        single_core_scores.append(seconds)
        if descriptor[1] and cpu_count() > 1:
            print(name, '(multi-core): ', end='', flush=True)
            seconds = run_test(descriptor[0], cpu_count())
            print(str(seconds), 'seconds')
            multi_core_scores.append(seconds)

    single_core_raw_score = sum(single_core_scores) / len(single_core_scores)
    single_core_score = SINGLE_CORE_REFERENCE / single_core_raw_score * 1000
    print('\nsingle core score: {}'.format(int(round(single_core_score))))
    if cpu_count() > 1:
        multi_core_raw_score = sum(multi_core_scores) / len(multi_core_scores)
        multi_core_score = MULTI_CORE_REFERENCE / multi_core_raw_score * 1000
        print('multi core score: {}'.format(int(round(multi_core_score))))


def download_test_data(urls):
    test_data = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        for name, url in urls.items():
            tmp_path = os.path.join(tmp_dir, name)
            wget.download(url, out=tmp_path, bar=None)
            if url.endswith('.gz'):
                open_func = gzip.open

            else:
                open_func = open

            with open_func(tmp_path) as fp:
                test_data[name] = fp.read()

        return test_data


def run_test(f, ncores, *args, **kwargs):
    if hasattr(f, '_data_urls'):
        test_data = download_test_data(f._data_urls)
        kwargs.update(test_data)

    if ncores > 1:
        with Pool(ncores) as pool:
            tick = time()
            f(ncores, pool.map, *args, **kwargs)
            tock = time()

    else:
        tick = time()
        f(ncores,
          lambda f, xlist: [f(x) for x in xlist],
          *args,
          **kwargs)

        tock = time()

    return tock - tick


if __name__ == '__main__':
    main()
