import pickle
from collections import defaultdict


class Classifier(object):
    def __init__(self):
        self.features = defaultdict(int)
        self.labels = defaultdict(int)
        self.feature_counts = defaultdict(lambda: defaultdict(int))
        self.total_count = 0

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as fh:
            features, labels, fc, total = pickle.load(fh)
        inst = cls()
        inst.features.update(features)
        inst.labels.update(labels)
        for feature, labels in fc.items():
            for label, ct in labels.items():
                inst.feature_counts[feature][label] = ct
        inst.total_count = total
        return inst

    def save(self, filename):
        fc = {}
        for feature, labels in self.feature_counts.items():
            fc[feature] = {}
            for label, ct in labels.items():
                fc[feature][label] = ct
        features = dict(self.features)
        labels = dict(self.labels)
        total = self.total_count
        with open(filename, 'wb') as fh:
            pickle.dump((features, labels, fc, total), fh)

    def train(self, features, labels):
        for label in labels:
            for feature in features:
                self.feature_counts[feature][label] += 1
                self.features[feature] += 1

            self.labels[label] += 1
        self.total_count += 1

    def feature_probability(self, feature, label):
        # get the count of this feature in the given label, this would
        # be "25" for "money"/"spam", or "5" for "money"/"ham"
        feature_count = self.feature_counts[feature][label]

        # get the count of documents with this label (e.g. 100)
        label_count = self.labels[label]

        if feature_count and label_count:
            # divide by the count of all features in the given category
            return float(feature_count) / label_count
        return 0

    def weighted_probability(self, feature, label, weight=1.0, ap=0.5):
        # calculate the "initial" probability that the given feature will
        # appear in the label -- this is .25 for "money"/"spam"
        initial_prob = self.feature_probability(feature, label)

        # sum the counts of this feature across all labels -- e.g.,
        # how many times overall does the word "money" appear? (30)
        feature_total = self.features[feature]

        # calculate weighted avg -- this is slightly different than what
        # we did in the above example and helps give a more evenly
        # weighted result and prevents us returning "0"
        return float((weight * ap) + (feature_total * initial_prob)) / (weight + feature_total)

    def document_probability(self, features, label):
        # calculate the probability these features match the label
        p = 1
        for feature in features:
            p *= self.weighted_probability(feature, label)
        return p

    def probability(self, features, label):
        if not self.total_count:
            # avoid doing a divide by zero
            return 0

        # calculate the probability that a document will have the given
        # label -- in our example this is (100 / 200)
        label_prob = float(self.labels[label]) / self.total_count

        # get the probabilities of each feature for the given label
        doc_prob = self.document_probability(features, label)

        # weight the document probability by the label probability
        return doc_prob * label_prob

    def classify(self, features, limit=5):
        # calculate the probability for each label
        probs = {}
        for label in self.labels.keys():
            probs[label] = self.probability(features, label)

        # sort the results so the highest probabilities come first
        return sorted(probs.items(), key=lambda (k,v): v, reverse=True)[:limit]