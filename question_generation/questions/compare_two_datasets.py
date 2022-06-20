# this script helps to compare generated clevrx files
import json

from tqdm import tqdm

filename = "/mnt/clevr-explanations/question_generation/questions/CLEVR_val_explanations_v0.7.10.json"

with open(filename) as f:
    data = json.load(f)


filename2 = (
    "/home/lsalewski11/akata-shared/lsalewski11/CLEVR_v1.0/questions/CLEVR_val_explanations_v0.7.13_readmetest.json"
)

with open(filename2) as f:
    data2 = json.load(f)

assert len(data["questions"]) == len(data2["questions"]), "Both datasets need to have the same number of samples!"

for published, reproduced in zip(tqdm(data["questions"]), data2["questions"]):
    p = published["factual_explanation"]
    r = reproduced["factual_explanation"]
    
    # ignore the "counter_factual_explanation" key
    published.pop("counter_factual_explanation")

    # try to directly compare, if that does not match try a set comparison
    # this is because python sets do not have a deterministic order, thus each generated dataset version may have a different ordering of the explanations.
    assert all(
        [
            set(v) == set(reproduced[k])
            for k, v in published.items()
            if v != reproduced[k]
        ]
    )

    if set(p) != set(r):
        print("---- Found a difference ----")
        print(published["factual_explanation"])
        print(reproduced["factual_explanation"])
        print()
