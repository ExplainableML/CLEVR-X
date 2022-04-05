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
2. [Citation](#Citation)

## CLEVR-X Dataset Download

The generated CLEVR-X dataset is available here: [CLEVR-X dataset](https://www.dropbox.com/sh/qe1wfahldk3pd7l/AADnsGTUInU5-eLCjyor0Iapa?dl=0) (~1.21 GB).
It is made up of two json files, which follow the general layout of the original CLEVR json files.

### Obtaining the CLEVR-X Split

Furthermore, there are two python pickle files (`train_images_ids_v0.7.10-recut.pkl` and `dev_images_ids_v0.7.10-recut.pkl`), which contain the image ids of all CLEVR-X train explanations and all CLEVR-X val explanations (both to be loaded from `CLEVR_train_explanations_v0.7.10.json`).

Each entry in `CLEVR_train_explanations_v0.7.10.json` has a field `image_index`, which must be part of `train_images_ids_v0.7.10-recut.pkl` for the CLEVR-X train split and which must be part of `dev_images_ids_v0.7.10-recut.pkl` for the CLEVR-X validation split.

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
