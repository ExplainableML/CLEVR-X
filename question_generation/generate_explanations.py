# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import print_function

import argparse
import html
import json
import os
import random
import time

import pandas as pd
from tqdm import tqdm
from treelib.exceptions import DuplicatedNodeIdError

from explanations import use_instantiated_template

"""
Generate synthetic explanations for questions and answers for CLEVR images. Input is a single
JSON file containing ground-truth scene information for all images, and output
is a single JSON file containing all generated questions, answers, and programs.

Questions are generated by expanding templates. Each template contains a single
program template and one or more text templates, both with the same set of typed
slots; by convention <Z> = Size, <C> = Color, <M> = Material, <S> = Shape.

Program templates may contain special nodes that expand into multiple functions
during instantiation; for example a "filter" node in a program template will
expand into a combination of "filter_size", "filter_color", "filter_material",
and "filter_shape" nodes after instantiation, and a "filter_unique" node in a
template will expand into some combination of filtering nodes followed by a
"unique" node.

Templates are instantiated using depth-first search; we are looking for template
instantiations where (1) each "unique" node actually refers to a single object,
(2) constraints in the template are satisfied, and (3) the answer to the question
passes our rejection sampling heuristics.

To efficiently handle (1) and (2), we keep track of partial evaluations of the
program during each step of template expansion. This together with the use of
composite nodes in program templates (filter_unique, relate_filter_unique) allow
us to efficiently prune the search space and terminate early when we know that
(1) or (2) will be violated.
"""


# TODO: Refactor!
# - use the tests to really modularize the code above.
# - to make the code more understandable, make things more visualized
#     - visualize the tree structure of the states variable. Maybe do so by using the moment a state is append to the list, because then "state" is the parent
#     - also templates could be visualized or pretty printed


parser = argparse.ArgumentParser()

# Inputs
parser.add_argument(
    "--input_scene_file",
    default="../output/CLEVR_scenes.json",
    help="JSON file containing ground-truth scene information for all images "
    + "from render_images.py",
)
parser.add_argument(
    "--input_questions_file",
    default="../output/CLEVR_questions.json",
    help="JSON file containing questions for all images.",
)
parser.add_argument(
    "--metadata_file",
    default="metadata.json",
    help="JSON file containing metadata about functions",
)
parser.add_argument(
    "--synonyms_json",
    default="synonyms.json",
    help="JSON file defining synonyms for parameter values",
)
parser.add_argument(
    "--template_dir",
    default="CLEVR_1.0_templates",
    help="Directory containing JSON templates for questions",
)

# Output
parser.add_argument(
    "--output_explanations_file",
    default="../output/CLEVR_explanations.json",
    help="The output file to write containing generated explanations",
)

# Control which and how many images to process
parser.add_argument(
    "--scene_start_idx",
    default=0,
    type=int,
    help="The image at which to start generating questions; this allows "
    + "question generation to be split across many workers",
)
parser.add_argument(
    "--num_scenes",
    default=0,
    type=int,
    help="The number of images for which to generate questions. Setting to 0 "
    + "generates questions for all scenes in the input file starting from "
    + "--scene_start_idx",
)

# Control the number of questions per image; we will attempt to generate
# templates_per_image * instances_per_template questions per image.
parser.add_argument(
    "--templates_per_image",
    default=10,
    type=int,
    help="The number of different templates that should be instantiated "
    + "on each image",
)
parser.add_argument(
    "--instances_per_template",
    default=1,
    type=int,
    help="The number of times each template should be instantiated on an image",
)

# Allow to specify a specific template family and index to run
parser.add_argument(
    "--template_fn",
    default=None,
    type=str,
    help="A specific template family as specified by the filename.",
)
parser.add_argument(
    "--template_idx",
    default=None,
    type=int,
    help="A specific template as specified by the index. Must be used with --template_fn to set a filename.",
)

# Misc
parser.add_argument(
    "--reset_counts_every",
    default=250,
    type=int,
    help="How often to reset template and answer counts. Higher values will "
    + "result in flatter distributions over templates and answers, but "
    + "will result in longer runtimes.",
)
parser.add_argument("--verbose", action="store_true", help="Print more verbose output")
parser.add_argument(
    "--time_dfs",
    action="store_true",
    help="Time each depth-first search; must be given with --verbose",
)
parser.add_argument(
    "--profile", action="store_true", help="If given then run inside cProfile"
)
parser.add_argument(
    "--seed", default=43, type=int, help="The seed to set for random.seed()"
)
parser.add_argument(
    "--log_to_dataframe",
    default=False,
    type=bool,
    help="whether to log the results to a dataframe. Decreases performance and may increase memory usage, but enables html output of examples",
)
# args = parser.parse_args()


TEMPLATE_ORDER = [
    "compare_integer.json",
    "comparison.json",
    "three_hop.json",
    "single_and.json",
    "same_relate.json",
    "single_or.json",
    "one_hop.json",
    "two_hop.json",
    "zero_hop.json",
]


def main(args):
    random.seed(args.seed)
    with open(args.metadata_file, "r") as f:
        metadata = json.load(f)
        dataset = metadata["dataset"]
        if dataset != "CLEVR-v1.0":
            raise ValueError('Unrecognized dataset "%s"' % dataset)

    functions_by_name = {}
    for f in metadata["functions"]:
        functions_by_name[f["name"]] = f
    metadata["_functions_by_name"] = functions_by_name

    # Load templates from disk
    # Key is (filename, file_idx)
    num_loaded_templates = 0
    templates = {}
    # FIXME: This does not look at the templates which are actually present, but using the template order is important so the matching of question to template is correct
    for fn in TEMPLATE_ORDER:
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(args.template_dir, fn), "r") as f:
            base = os.path.splitext(fn)[0]
            for i, template in enumerate(json.load(f)):
                num_loaded_templates += 1
                key = (fn, i)
                templates[key] = template
    print("Read %d templates from disk" % num_loaded_templates)

    def reset_counts():
        # Maps a template (filename, index) to the number of questions we have
        # so far using that template
        template_counts = {}
        # Maps a template (filename, index) to a dict mapping the answer to the
        # number of questions so far of that template type with that answer
        template_answer_counts = {}
        node_type_to_dtype = {n["name"]: n["output"] for n in metadata["functions"]}
        for key, template in templates.items():
            template_counts[key[:2]] = 0
            final_node_type = template["nodes"][-1]["type"]
            final_dtype = node_type_to_dtype[final_node_type]
            answers = metadata["types"][final_dtype]
            if final_dtype == "Bool":
                answers = [True, False]
            if final_dtype == "Integer":
                if metadata["dataset"] == "CLEVR-v1.0":
                    answers = list(range(0, 11))
            template_answer_counts[key[:2]] = {}
            for a in answers:
                template_answer_counts[key[:2]][a] = 0
        return template_counts, template_answer_counts

    template_counts, template_answer_counts = reset_counts()

    all_questions = []
    with open(args.input_questions_file, "r") as f:
        questions_data = json.load(f)
        all_questions = questions_data["questions"]

    # Read file containing input scenes
    all_scenes = []
    with open(args.input_scene_file, "r") as f:
        scene_data = json.load(f)
        all_scenes = scene_data["scenes"]
        scene_info = scene_data["info"]

    begin = args.scene_start_idx
    if args.num_scenes > 0:
        end = args.scene_start_idx + args.num_scenes
        all_scenes = all_scenes[begin:end]
        all_questions = all_questions[begin:end]
    else:
        all_scenes = all_scenes[begin:]
        all_questions = all_questions[begin:]

    # Read synonyms file
    with open(args.synonyms_json, "r") as f:
        synonyms = json.load(f)

    df = pd.DataFrame(
        columns=[
            "Family",
            "ID",
            "Instantiated Language",
            "Image",
            "Answer",
            "Factual Answer",
        ]
    )
    questions = []
    scene_count = 0
    for i, question in tqdm(
        enumerate(all_questions), total=len(all_questions), smoothing=0.05
    ):
        scene_fn: str = question["image_filename"]
        scene_struct_candidates = [
            s for s in all_scenes if s["image_filename"] == scene_fn
        ]
        if len(scene_struct_candidates) != 1:
            print(f"no matching scene graph loaded for fn: {scene_fn}")
            continue

        scene_struct = scene_struct_candidates[0]
        assert scene_struct["image_filename"] == question["image_filename"]

        if args.verbose:
            print(f"starting question {scene_fn} ({i + 1} / {len(all_questions)})")

        (fn, idx), cur_template = list(templates.items())[
            question["question_family_index"]
        ]

        if args.template_fn is not None and args.template_idx is not None:
            if args.template_fn != fn or args.template_idx != idx:
                print(
                    "Skipped question as the given template filename and index does not match whats required via the args."
                )
                continue

        if args.verbose:
            print("Generating Explanations for template ", fn, idx)
        if args.time_dfs and args.verbose:
            tic = time.time()

        try:
            ef = use_instantiated_template(
                scene_struct,
                cur_template,
                question,
                metadata,
                template_answer_counts[(fn, idx)].copy(),
                synonyms,
                (fn, idx),
                max_instances=args.instances_per_template,
                verbose=args.verbose,
            )

            if args.time_dfs and args.verbose:
                toc = time.time()
                print("that took ", toc - tic)

            image_index = int(os.path.splitext(scene_fn)[0].split("_")[-1])
            for f in ef:
                questions.append(
                    {
                        **question,
                        **{
                            "factual_explanation": f,
                            "counter_factual_explanation": [],
                        },
                    }
                )

                if args.log_to_dataframe:
                    img = f'<img src="{question["image_filename"]}">'
                    df = df.append(
                        {
                            "Family": fn,
                            "ID": idx,
                            "Nodes": html.escape(
                                json.dumps(cur_template["nodes"], indent=4)
                            ).replace("\n", "<br>"),
                            # "Constraints": html.escape(json.dumps(cur_template["constraints"], indent=4)).replace("\n", "<br>"),
                            # "Instantiated Nodes": json.dumps(question["program"], indent=4).replace("\n", "<br>"),
                            # "Language Template": "<br><br>".join([html.escape(t) for t in cur_template["text"]]),
                            "Instantiated Language": question["question"],
                            "Image": img,
                            "Answer": question["answer"],
                            "Factual Answer": "<br><br>".join(f),
                            # "Counter Factual Answer": "<br><br>".join("<br>".join(x) for x in cf)
                        },
                        ignore_index=True,
                    )
        except DuplicatedNodeIdError:
            print(f"ERROR: Malformed program, skipping item {i}")
            pass

    data = {
        "info": scene_info,
        "questions": questions,
    }
    with open(args.output_explanations_file, "w") as f:
        print("Writing output to %s" % args.output_explanations_file)
        json.dump(data, f)

    # save this into the val images folder for the images to appear
    # print(df.sort_values(['Family', 'ID']).to_html(escape=False))
    if args.log_to_dataframe:
        try:
            split = "val"
            case = ""
            version = "v0.7.11"

            save_path = f"./images/{split}{case}/debug_{version}.html"

            number_of_items = 50

            subset_from_families = pd.concat(
                [
                    df.sort_values(["Family"])
                    .query(f"Family == '{family}.json'")
                    .iloc[:number_of_items]
                    for family in [
                        "compare_integer",
                        "comparison",
                        "one_hop",
                        "same_relate",
                        "three_hop",
                        "two_hop",
                        "zero_hop",
                        "single_and",
                        "single_or",
                    ]
                ]
            )

            subset_from_families.to_html(escape=False, buf=save_path)
        except FileNotFoundError:
            print("File not found, no df html saved")

    # for easier testing also return the data
    return data


if __name__ == "__main__":
    args = parser.parse_args()
    if args.profile:
        import cProfile

        cProfile.run("main(args)")
    else:
        main(args)
