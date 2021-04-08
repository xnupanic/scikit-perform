"""
Copyright 2021 Jerrad M. Genson

This Source Code Form is subject to the terms of the BSD-2-Clause license.
If a copy of the BSD-2-Clause license was not distributed with this
file, You can obtain one at https://opensource.org/licenses/BSD-2-Clause.

"""

import lzma
import math
import hashlib
import functools
from collections import ChainMap
from functools import partial
import xml.etree.ElementTree as ET
from io import StringIO

import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn import svm
from sklearn import ensemble
from sklearn.manifold import LocallyLinearEmbedding
from sklearn.model_selection import GridSearchCV

NASA_DATA = 'https://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/nasa/nasa.xml.gz'
HAMLET = 'https://gist.githubusercontent.com/provpup/2fc41686eab7400b796b/raw/b575bd01a58494dfddc1d6429ef0167e709abf9b/hamlet.txt'
ENGLISH_WORDS = 'https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt'
SHUTTLE_DATA = 'https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/shuttle/shuttle.tst'
EL_NINO = 'https://archive.ics.uci.edu/ml/machine-learning-databases/el_nino-mld/tao-all2.dat.gz'
PROTEIN_SEQUENCE = 'https://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/SwissProt/SwissProt.xml.gz'


def with_data(**kwargs):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        wrapper._data_urls = kwargs
        return wrapper

    return decorator


@with_data(hamlet=HAMLET, words=ENGLISH_WORDS)
def hamlet_word_count(ncores, map, hamlet, words):
    words = words.split()
    total_words = len(words)
    job_words = math.floor(total_words / ncores)
    slices = []
    for core in range(ncores):
        start = core * job_words
        if core + 1 == ncores:
            end = total_words - 1

        else:
            end = (core + 1) * job_words

        slices.append(words[start:end])

    count_partial = partial(count_occurences, hamlet)
    disjoint_word_count = map(count_partial, slices)
    word_count = dict(ChainMap(*disjoint_word_count))

    return word_count


def count_occurences(text, words):
    return {word: text.count(word) for word in words}


@with_data(test_data=NASA_DATA)
def xml_parsing(_1, _2, test_data):
    ET.fromstring(test_data)


@with_data(test_data=NASA_DATA)
def lzma_compression(_1, _2, test_data):
    lzma.compress(test_data)


@with_data(test_data=PROTEIN_SEQUENCE)
def sha512(_1, _2, test_data):
    m = hashlib.sha3_512()
    m.update(test_data)
    m.digest()

@with_data(shuttle_data=SHUTTLE_DATA)
def support_vector_machine(ncores, _, shuttle_data):
    param_grid = [
        {'model__C': [1, 10, 100, 1000], 'model__kernel': ['linear']},
        {'model__C': [1, 10, 100, 1000], 'model__gamma': [0.001, 0.0001], 'model__kernel': ['rbf']},
    ]

    inputs, targets = parse_shuttle_data(shuttle_data)
    pipeline = Pipeline(steps=[('scale', StandardScaler()), ('model', svm.SVC())])
    estimator = GridSearchCV(pipeline, param_grid, cv=2, n_jobs=ncores)
    estimator.fit(inputs, targets)


@with_data(shuttle_data=SHUTTLE_DATA)
def random_forest(ncores, _, shuttle_data):
    param_grid = [
        {
            'criterion': ['gini', 'entropy'],
            'min_samples_split': list(range(2, 11))
        }
    ]

    inputs, targets = parse_shuttle_data(shuttle_data)
    estimator = GridSearchCV(ensemble.RandomForestClassifier(n_estimators=500),
                             param_grid,
                             cv=2,
                             n_jobs=ncores)

    estimator.fit(inputs, targets)


@with_data(shuttle_data=SHUTTLE_DATA)
def locally_linear_embedding(ncores, _, shuttle_data):
    inputs, _ = parse_shuttle_data(shuttle_data)
    embedding = LocallyLinearEmbedding(eigen_solver='dense', n_jobs=ncores)
    embedding.fit_transform(inputs[:4000])


def parse_shuttle_data(shuttle_data):
    shuttle_data = StringIO(shuttle_data)
    shuttle_df = pd.read_csv(shuttle_data, sep=' ')
    shuttle_array = shuttle_df.to_numpy()
    inputs = shuttle_array[:, [0, -2]]
    targets = shuttle_array[:, -1]

    return inputs, targets
