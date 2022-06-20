# CLEVR-X: A Visual Reasoning Dataset for Natural Language Explanations

By <a href='https://www.eml-unitue.de/people/leonard-salewski'>Leonard Salewski</a>, <a href='https://www.eml-unitue.de/people/almut-sophia-koepke'>A. Sophia Koepke</a>, <a href='https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/computergrafik/lehrstuhl/mitarbeiter/prof-dr-ing-hendrik-lensch/'>Hendrik Lensch</a> and <a href='https://www.eml-unitue.de/people/zeynep-akata'>Zeynep Akata</a>.
Published in [Springer LNAI xxAI](https://human-centered.ai/springer-lnai-xxai/). A preprint is available on [arXiv](https://arxiv.org/abs/2204.02380).

<!-- >📋 Optional: include a link to demos, blog posts and tutorials -->

This repository is the official implementation of [CLEVR-X: A Visual Reasoning Dataset for Natural Language Explanations](https://explainableml.github.io/CLEVR-X/). It contains code to generate the CLEVR-X dataset and a [PyTorch](https://pytorch.org/) dataset implementation.

Below is an example from the CLEVR dataset extended with CLEVR-X's natural language explanation:

![A synthetically rendered image of a small cyan metallic cylinder, a large purple metallic sphere, a large blue matte cube, a large brown matte cylinder and a large green metallic cylinder (from front to back) on an infinite flat matte gray surface.](images/CLEVR_val_005182.png)
> **Question:** There is a purple metallic ball; what number of cyan objects are right of it?

> **Answer**: 1

> **Explanation**: There is a cyan cylinder which is on the right side of the purple metallic ball.

## Overview

This repository contains instructions for:

1. [CLEVR-X Dataset Download](#CLEVR-X-Dataset-Download)
2. [CLEVR-X Dataset Generation](#CLEVR-X-Dataset-Generation)
3. [Model Results](#Results)
4. [Contribution and License](#Contributing)
5. [Citation](#Citation)

## CLEVR-X Dataset Download

The generated CLEVR-X dataset is available here: [CLEVR-X dataset](https://www.dropbox.com/sh/qe1wfahldk3pd7l/AADnsGTUInU5-eLCjyor0Iapa?dl=0) (~1.21 GB).

The download includes two JSON files, which contain the explanations for all CLEVR train and CLEVR validation questions (`CLEVR_train_explanations_v0.7.10.json` and  `CLEVR_val_explanations_v0.7.10.json` respectively).
The general layout of the JSON files follows the original CLEVR JSON files. The `info` key contains general information, whereas the `questions` key contains the dataset itself. The latter is a list of dictionaries, where each dictionary is one sample of the CLEVR-X dataset.

Furthermore, we provide two python pickle files at the same link. Those contain a list of the image indices of the CLEVR-X train and CLEVR-X validation subsets (which are both part of the CLEVR train subset.)

Note, that we do not provide the images of the CLEVR dataset, which can be downloaded from the original [CLEVR project page](https://cs.stanford.edu/people/jcjohns/clevr/).

### Obtaining the CLEVR-X Splits

As stated above, the two python pickle files (`train_images_ids_v0.7.10-recut.pkl` and `dev_images_ids_v0.7.10-recut.pkl`) contain the image indices of all CLEVR-X train explanations and all CLEVR-X validation explanations.

#### Train

To obtain the train samples, iterate through the samples in `CLEVR_train_explanations_v0.7.10.json` and use those samples, whose `image_index` is in the list contained in `train_images_ids_v0.7.10-recut.pkl`.

#### Validation

To obtain the validation samples, iterate through the samples in `CLEVR_train_explanations_v0.7.10.json` and use those samples, whose `image_index` is in the list contained in `dev_images_ids_v0.7.10-recut.pkl`.

#### Test

All samples from the CLEVR _validation_ subset (`CLEVR_val_explanations_v0.7.10.json`) are used for the CLEVR-X **test** subset.

## CLEVR-X Dataset Generation

The following sections explain how to generate the CLEVR-X dataset.

### Requirements

The required libraries for generating the CLEVR-X dataset can be found in the environment.yaml file. To create an environment and to install the requirements use [conda](https://docs.conda.io/en/latest/):

```setup
conda env create --file environment.yaml
```

Activate it with:

```setup
conda activate clevr_explanations
```

### CLEVR Dataset Download

As CLEVR-X uses the same questions and images as CLEVR, it is necessary to download the [CLEVR dataset](https://cs.stanford.edu/people/jcjohns/clevr/). Follow the instructions on the [CLEVR dataset website](https://cs.stanford.edu/people/jcjohns/clevr/) to download the original dataset (images, scene graphs and questions & answers).
The extracted files should be located in a folder called `CLEVR_v1.0` also known as `$CLEVR_ROOT`.
For further instructions and information about the original CLEVR code, it could also be helpful to refer to the [CLEVR GitHub repository](https://github.com/facebookresearch/clevr-dataset-gen).

### Training Subset

First change into the `question_generation` directory:

```bash
cd question_generation
```

To generate explanations for the CLEVR training subset run this command:

```bash
python generate_explanations.py \
    --input_scene_file $CLEVR_ROOT/scenes/CLEVR_train_scenes.json \
    --input_questions_file $CLEVR_ROOT/questions/CLEVR_train_questions.json \
    --output_explanations_file $CLEVR_ROOT/questions/CLEVR_train_explanations_v0.7.13.json \
    --seed "43" \
    --metadata_file ./metadata.json
```

This generation takes about 6 hours on an Intel(R) Xeon(R) Gold 5220 CPU @ 2.20GHz.
Note, setting the `--log_to_dataframe` flag to `true` may increase the generation time significantly, but allows dumping (parts of) the dataset as an HTML table.

### Validation Subset

First change into the `question_generation` directory:

```bash
cd question_generation
```

To generate explanations for the CLEVR validation subset run this command:

```bash
python generate_explanations.py \
    --input_scene_file $CLEVR_ROOT/scenes/CLEVR_val_scenes.json \
    --input_questions_file $CLEVR_ROOT/questions/CLEVR_val_questions.json \
    --output_explanations_file $CLEVR_ROOT/questions/CLEVR_val_explanations_v0.7.13.json \
    --seed "43" \
    --metadata_file ./metadata.json
```

This generation takes less than 1 hour on an Intel(R) Xeon(R) Gold 5220 CPU @ 2.20GHz.
Note, setting the `--log_to_dataframe` flag to `true` may increase the generation time significantly, but allows dumping (parts of) the dataset as an HTML table.

Both commands use the `--input_scene_file`, `--input_questions_file` and the `--metadata_file` provided by the original [CLEVR](https://cs.stanford.edu/people/jcjohns/clevr/) dataset. You can use any name for the `--output_explanations_file` argument, but the dataloader expects it in the format `CLEVR_<split>_explanations_<version>.json`.

### Splits

Note, that the original CLEVR test set does not have publically accessible scene graphs and functional programs. Thus, we use the CLEVR validation set as the CLEVR-X test subset. The following code generates a **new** split of the CLEVR training set into the CLEVR-X training and validation subsets:

```bash
cd question_generation
python dev_split.py --root $CLEVR_ROOT
```

As each image comes with ten questions, the split is performed alongside the images instead of individual dataset samples. The code stores the image indices of each split in two separate python pickle files (named `train_images_ids_v0.7.10-recut.pkl` and `dev_images_ids_v0.7.10-recut.pkl`). We have published our files alongside with the dataset download and recommend using those indices.

## Results

Different baselines and VQA-X models achieve the following performance on CLEVR-X:

| Model name         |       Accuracy  | [BLEU](https://aclanthology.org/P02-1040/)           | [METEOR](https://aclanthology.org/W05-0909/)         | [ROUGE-L](https://aclanthology.org/W04-1013/)        | [CIDEr](https://openaccess.thecvf.com/content_cvpr_2015/papers/Vedantam_CIDEr_Consensus-Based_Image_2015_CVPR_paper.pdf)          |
| ------------------ |---------------- | -------------- | -------------- | -------------- | -------------- |
| Random Words       |       3.6%         |     0.0           | 8.4               |        11.4        |     5.9           |
| Random Explanations|       3.6%         |     10.9           |   16.6             |     35.3           |      30.4          |
| [PJ-X](https://openaccess.thecvf.com/content_cvpr_2018/papers/Park_Multimodal_Explanations_Justifying_CVPR_2018_paper.pdf)               |       80.3%         |      78.8          |        52.5        |      85.8          |       566.8         |
| [FM](https://arxiv.org/abs/1809.02805)                 |       63.0%         |        87.4        |     58.9           |    93.4            |     639.8           |

For more information on the baselines and models, check the respective publications and our CLEVR-X publication itself.

## Contributing & License

For information on the license please look into the `LICENSE` file.

## Citation

If you use CLEVR-X in any of your works, please use the following bibtex entry to cite it:

```tex
@inproceedings{salewski2022clevrx,
    title     = {CLEVR-X: A Visual Reasoning Dataset for Natural Language Explanations},
    author    = {Leonard Salewski and A. Sophia Koepke and Hendrik P. A. Lensch and Zeynep Akata},
    booktitle = {xxAI - Beyond explainable Artificial Intelligence},
    pages     = {85--104},
    year      = {2022},
    publisher = {Springer}
}
```
