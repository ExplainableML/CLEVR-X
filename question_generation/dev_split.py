import os
import pickle
import shutil
import random
from random import shuffle
import argparse, json, os

# This is the same seed as used in the rest of the repository.
random.seed(43)

parser = argparse.ArgumentParser()
parser.add_argument("--root", default="./")
parser.add_argument("--split", default="train")
parser.add_argument("--case", default="")
parser.add_argument("--version", default="v0.7.10")
parser.add_argument("--rel_dev_size", default=0.2)


def dev_split_function(
    root: str,
    split: str = "train",
    case: str = "",
    version: str = "v0.7.10",
    rel_dev_size: float = 0.2,
):
    """
    Splits a original CLEVR train subset into a CLEVRX train and dev subsets.add_constant()

    Args:
        root (str): The root path to the source files.
        split (str): The split to load, which will be splited. Only "train" is currently allowed.
        case (str): The case to split, needed for support of CLEVR CoGenT.
        rel_dev_size (float, optional): The relative size of the resulting dev set. 0.2 was used for the published CLEVR-X. Defaults to 0.2.
    """

    # BUG: should load the pickle files with the IDs!

    assert 0 < rel_dev_size < 1, "relative dev size has to be between 0 and 1"
    assert split == "train", "can only split train into new_train + dev"

    features_path = os.path.join(root, "questions")
    complete_path = os.path.join(
        features_path, f"CLEVR_{split}{case}_explanations_{version}.json"
    )
    with open(complete_path) as f:
        all_data = json.load(f)
        data = all_data["questions"]

    assert len(data) == 699964, "must load the original train split!"

    print("Starting to split original CLEVR train into CLEVRX train and dev!")
    # the "recut" appendix indicataes it is a version which has been recutted. It is also used to detect the dev has to be used.
    new_version = f"{version}-recut"
    assert new_version != version, "must save with new version name!"
    print(f"New version name is: {new_version}")

    # the split needs to be based on the images
    all_images = list(set(d["image_index"] for d in data))
    shuffle(all_images)

    # sample the dev set away
    dev_images = set(all_images[: int(len(all_images) * rel_dev_size)])
    remaining_train_images = set(all_images) - set(dev_images)

    # save the splits as new dataset pickle files
    for split, images in zip(["dev", "train"], [dev_images, remaining_train_images]):
        print(f"Processing {split}...")
        # select the subset of the data
        subset_data = [d for d in data if d["image_index"] in images]
        assert len(subset_data) > 0

        # save the subset of data
        new_file_path = f"{features_path}/CLEVR_{split}{case}_explanations_{new_version}.json"
        assert not os.path.exists(new_file_path), "newly splitted file already exists!"
        with open(new_file_path, "w") as f:
            all_new_data = {
                "info": all_data["info"],
                "questions": subset_data,
            }
            json.dump(all_new_data, f)

        # save the ids
        image_ids_path = f"{features_path}/CLEVR_{split}{case}_images_ids_{new_version}.pkl"
        assert not os.path.exists(image_ids_path), "new image_ids file already exists!"
        with open(
            image_ids_path, "wb"
        ) as f2:
            pickle.dump(images, f2)

    # Copy val split with new name, so future runs can use the new version name without code changes.
    print(f"Processing val...")

    # the validation file stays unchanged, but also gets the new version name. It needs to be loaded in place of a test file for the test subset.
    src = os.path.join(features_path, f"CLEVR_val{case}_explanations_{version}.json")
    dst = os.path.join(
        features_path, f"CLEVR_val{case}_explanations_{new_version}.json"
    )
    shutil.copyfile(src, dst)

    print("Split was successfully performed.")


if __name__ == "__main__":
    args = parser.parse_args()
    dev_split_function(
        root=args.root,
        split=args.split,
        case=args.case,
        version=args.version,
        rel_dev_size=args.rel_dev_size,
    )
