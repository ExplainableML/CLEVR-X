# CLEVR-X: A Visual Reasoning Dataset for Natural Language Explanations

By <a href='https://www.eml-unitue.de/people/leonard-salewski'>Leonard Salewski</a>, <a href='https://www.eml-unitue.de/people/almut-sophia-koepke'>A. Sophia Koepke</a>, <a href='https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/computergrafik/lehrstuhl/mitarbeiter/prof-dr-ing-hendrik-lensch/'>Hendrik Lensch</a> and <a href='https://www.eml-unitue.de/people/zeynep-akata'>Zeynep Akata</a>.
To be published in [Springer LNAI xxAI](https://human-centered.ai/springer-lnai-xxai/).

<!-- >📋 Optional: include a link to demos, blog posts and tutorials -->

This repository is the official implementation of [CLEVR-X: A Visual Reasoning Dataset for Natural Language Explanations](todo). It contains code to generate the CLEVR-X dataset and a [PyTorch](https://pytorch.org/) dataset implementation.

Below is an example from the CLEVR dataset extended with CLEVR-X's natural language explanation:

![A synthetically rendered image of a small cyan metallic cylinder, a large purple metallic sphere, a large blue matte cube, a large brown matte cylinder and a large green metallic cylinder (from front to back) on an infinite flat matte gray surface.](images/CLEVR_val_005182.png)
> **Question:** There is a purple metallic ball; what number of cyan objects are right of it?

> **Answer**: 1

> **Explanation**: There is a cyan cylinder which is on the right side of the purple metallic ball.

## Overview

This repository contains instructions for:

1. [CLEVR-X Dataset Download](#CLEVR-X-Dataset-Download)
2. [CLEVR-X Dataset Generation](#CLEVR-X-Dataset-Generation)
3. [Citation](#Citation)

## CLEVR-X Dataset Download

The generated CLEVR-X dataset is available here: [CLEVR-X dataset](https://www.dropbox.com/sh/qe1wfahldk3pd7l/AADnsGTUInU5-eLCjyor0Iapa?dl=0) (~1.21 GB).

The download includes two JSON files, which contain the explanations for all CLEVR train and CLEVR validation questions (`CLEVR_train_explanations_v0.7.10.json` and  `CLEVR_val_explanations_v0.7.10.json` respectively).
The general layout of the JSON files follows the original CLEVR JSON files. The `info` key contains general information, whereas the `questions` key contains the dataset itself. The latter is a list of dictionaries, where each dictionary is one sample of the CLEVR-X dataset.

Furthermore, we provide two python pickle files at the same link. Those contain a list of the image indices of the CLEVR-X train and CLEVR-X validation subsets (which are both part of the CLEVR train subset.)

Note, that we do not provide the images of the CLEVR dataset, which can be downloaded from the original [CLEVR project page](https://cs.stanford.edu/people/jcjohns/clevr/).

### Obtaining the CLEVR-X Splits

As stated above, the two python pickle files (`train_images_ids_v0.7.10-recut.pkl` and `dev_images_ids_v0.7.10-recut.pkl`) contain the image indices of all CLEVR-X train explanations and all CLEVR-X validation explanations.

To separate these subsets, one must iterate through the samples in `CLEVR_train_explanations_v0.7.10.json` and check whether the `image_index` of each sample is either in the list contained in  `train_images_ids_v0.7.10-recut.pkl` or in the list contained in `dev_images_ids_v0.7.10-recut.pkl`.

## CLEVR-X Dataset Generation

Coming soon.

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
