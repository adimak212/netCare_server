from src.algorithm.version2.domain.pattern import Pattern
from src.algorithm.version2.domain.resources import Resources
from src.algorithm.version2.domain.demand_vector import DemandVector


def pattern_from_mongo(doc):

    return Pattern(
        bin_type=doc["bin_type"],

        counts=DemandVector(
            **doc["counts"]
        ),

        total_resources=Resources(
            **doc["total_resources"]
        ),

        bin_capacity=Resources(
            **doc["bin_capacity"]
        )
    )


class PatternRepository:

    def __init__(self, collection):
        self.collection = collection

    def load_patterns(self, bin_type):

        docs = list(
            self.collection.find(
                {"bin_type": bin_type}
            )
        )

        return [
            pattern_from_mongo(x)
            for x in docs
        ]

    def save_patterns(
        self,
        bin_type,
        patterns
    ):

        docs = [
            p.as_dict()
            for p in patterns
        ]

        if docs:
            self.collection.insert_many(docs)